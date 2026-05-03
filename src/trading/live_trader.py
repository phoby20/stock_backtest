"""
키움 OpenAPI+ 기반 실시간 자동매매 엔진
- RSI + MACD 복합 전략 사용
- 실시간 체결가 수신 → 지표 계산 → 매수/매도 자동 실행
"""
import logging
import sys
from collections import deque
from datetime import datetime
from typing import Optional

import pandas as pd
from PyQt5.QtWidgets import QApplication

from src.broker.kiwoom import KiwoomAPI, ORDER_BUY, ORDER_SELL, PRICE_MARKET
from src.indicators.rsi import calculate_rsi
from src.indicators.macd import calculate_macd, detect_golden_cross, detect_dead_cross
from config import Config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("trade_log.txt", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)


class LiveTrader:
    def __init__(
        self,
        ticker: str,
        account: str,
        rsi_period: int = Config.RSI_PERIOD,
        oversold: float = Config.RSI_OVERSOLD,
        overbought: float = Config.RSI_OVERBOUGHT,
        macd_fast: int = 12,
        macd_slow: int = 26,
        macd_signal: int = 9,
        buy_ratio: float = Config.BUY_RATIO,
        paper: bool = False,
    ):
        self.ticker    = ticker
        self.account   = account
        self.rsi_period  = rsi_period
        self.oversold    = oversold
        self.overbought  = overbought
        self.macd_fast   = macd_fast
        self.macd_slow   = macd_slow
        self.macd_signal = macd_signal
        self.buy_ratio   = buy_ratio
        self.paper       = paper  # True = 모의매매 (실제 주문 미전송)

        self.api: Optional[KiwoomAPI] = None

        # RSI 계산에 필요한 최소 데이터 수 (slow EMA + signal)
        self._min_bars = max(rsi_period, macd_slow + macd_signal) + 5
        self._prices: deque[float] = deque(maxlen=self._min_bars + 50)

        self._position   = False   # 현재 포지션 보유 여부
        self._hold_qty   = 0       # 보유 수량
        self._hold_price = 0.0     # 평균 매수가

        # 직전 신호 저장 (중복 주문 방지)
        self._last_signal = "HOLD"

    # ── 초기화 ─────────────────────────────────────────────────
    def _load_history(self):
        """일봉 데이터로 초기 가격 큐 채우기"""
        logger.info(f"[초기화] {self.ticker} 일봉 데이터 로드 중...")
        ohlcv = self.api.get_ohlcv(self.ticker, count=self._min_bars)
        for row in reversed(ohlcv):          # 오래된 순서로 삽입
            self._prices.append(float(row["close"]))
        logger.info(f"[초기화] {len(self._prices)}개 봉 로드 완료")

    # ── 지표 계산 & 신호 판단 ──────────────────────────────────
    def _compute_signal(self) -> str:
        if len(self._prices) < self._min_bars:
            return "HOLD"

        prices = pd.Series(list(self._prices))

        rsi = calculate_rsi(prices, period=self.rsi_period)
        macd_line, sig_line, _ = calculate_macd(
            prices, fast=self.macd_fast, slow=self.macd_slow, signal=self.macd_signal
        )

        cur_rsi  = rsi.iloc[-1]
        golden   = detect_golden_cross(macd_line, sig_line).iloc[-1]
        dead     = detect_dead_cross(macd_line, sig_line).iloc[-1]
        rsi_fall = cur_rsi < rsi.iloc[-2]

        logger.debug(f"RSI={cur_rsi:.2f} | MACD_golden={golden} | MACD_dead={dead}")

        if cur_rsi <= self.oversold and golden:
            return "BUY"
        if cur_rsi >= self.overbought and rsi_fall and dead:
            return "SELL"
        return "HOLD"

    # ── 주문 실행 ──────────────────────────────────────────────
    def _execute_buy(self, price: float):
        deposit = self.api.get_deposit(self.account)
        budget  = int(deposit * self.buy_ratio)
        qty     = budget // int(price)

        if qty <= 0:
            logger.warning(f"[매수 불가] 예수금 부족: {deposit:,}원")
            return

        logger.info(
            f"[매수 신호] {self.ticker} | 현재가:{price:,.0f} | "
            f"수량:{qty}주 | 금액:{qty*price:,.0f}원"
            + (" [모의]" if self.paper else "")
        )
        if not self.paper:
            self.api.send_order(self.account, self.ticker, ORDER_BUY, qty)

        self._position   = True
        self._hold_qty   = qty
        self._hold_price = price

    def _execute_sell(self, price: float):
        qty = self._hold_qty
        if qty <= 0:
            return

        profit     = (price - self._hold_price) * qty
        profit_pct = (price / self._hold_price - 1) * 100
        logger.info(
            f"[매도 신호] {self.ticker} | 현재가:{price:,.0f} | "
            f"수량:{qty}주 | 손익:{profit:+,.0f}원 ({profit_pct:+.2f}%)"
            + (" [모의]" if self.paper else "")
        )
        if not self.paper:
            self.api.send_order(self.account, self.ticker, ORDER_SELL, qty)

        self._position   = False
        self._hold_qty   = 0
        self._hold_price = 0.0

    # ── 실시간 체결 콜백 ───────────────────────────────────────
    def _on_price(self, ticker: str, price: float):
        """실시간 가격 수신 시마다 호출"""
        self._prices.append(price)
        signal = self._compute_signal()

        ts = datetime.now().strftime("%H:%M:%S")
        rsi_val = ""
        if len(self._prices) >= self._min_bars:
            ps = pd.Series(list(self._prices))
            rsi_val = f" | RSI:{calculate_rsi(ps, self.rsi_period).iloc[-1]:.2f}"

        print(f"\r[{ts}] {ticker} {price:,.0f}원{rsi_val} | 신호:{signal}  ", end="", flush=True)

        # 중복 신호 방지
        if signal == self._last_signal:
            return
        self._last_signal = signal

        if signal == "BUY" and not self._position:
            print()
            self._execute_buy(price)
        elif signal == "SELL" and self._position:
            print()
            self._execute_sell(price)

    # ── 실행 진입점 ────────────────────────────────────────────
    def run(self):
        app = QApplication(sys.argv)
        self.api = KiwoomAPI()

        logger.info("=" * 55)
        logger.info(f"  RSI+MACD 자동매매 시작")
        logger.info(f"  종목: {self.ticker} | 계좌: {self.account}")
        logger.info(f"  전략: RSI({self.rsi_period}) + MACD({self.macd_fast}/{self.macd_slow}/{self.macd_signal})")
        logger.info(f"  매수: RSI≤{self.oversold} + 골든크로스 | 매도: RSI≥{self.overbought} + 데드크로스")
        logger.info(f"  모드: {'모의매매 (주문 미전송)' if self.paper else '실제매매'}")
        logger.info("=" * 55)

        if not self.api.login():
            logger.error("로그인 실패. 키움 OpenAPI+ 클라이언트를 확인하세요.")
            sys.exit(1)

        logger.info(f"로그인 성공 | 계좌: {self.api.get_account_list()}")
        self._load_history()
        self.api.subscribe_real(self.ticker, self._on_price)

        logger.info(f"{self.ticker} 실시간 감시 시작 (종료: Ctrl+C)")
        try:
            app.exec_()
        except KeyboardInterrupt:
            logger.info("자동매매 종료")
        finally:
            self.api.unsubscribe_real(self.ticker)
