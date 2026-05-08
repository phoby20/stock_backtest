"""
실시간 자동매매 엔진 (브로커 독립)
- 키움증권 / 한국투자증권 모두 지원 (BrokerBase Protocol)
- 역사 데이터: yfinance (크로스 플랫폼)
- NYSE 장 시간 감지: 정규장에서만 매매, 섬머타임 자동 반영
- 프리장 / 애프터장: 가격 수신 계속, 매매 중단
"""
import logging
import threading
import time
from collections import deque
from datetime import datetime
from typing import Optional

import pandas as pd

from src.broker.base import BrokerBase
from src.indicators.rsi import calculate_rsi
from src.indicators.macd import calculate_macd, detect_golden_cross, detect_dead_cross
from src.utils.market_hours import (
    get_session, session_label, et_clock_str, is_market_open,
)
from config import Config

logger = logging.getLogger(__name__)


class LiveTrader:
    def __init__(
        self,
        broker: BrokerBase,
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
        self.broker    = broker
        self.ticker    = ticker
        self.account   = account
        self.rsi_period  = rsi_period
        self.oversold    = oversold
        self.overbought  = overbought
        self.macd_fast   = macd_fast
        self.macd_slow   = macd_slow
        self.macd_signal = macd_signal
        self.buy_ratio   = buy_ratio
        self.paper       = paper

        self._min_bars = max(rsi_period, macd_slow + macd_signal) + 5
        self._prices: deque[float] = deque(maxlen=self._min_bars + 50)

        self._position    = False
        self._hold_qty    = 0
        self._hold_price  = 0.0
        self._last_signal = "HOLD"
        self._last_session: Optional[str] = None   # 세션 변경 감지용
        self._running     = False
        self._stop_event  = threading.Event()      # 즉시 중단용

    # ── 초기화 ─────────────────────────────────────────────────
    def _load_history(self):
        """yfinance 로 초기 가격 큐 채우기"""
        import yfinance as yf
        logger.info(f"[초기화] {self.ticker} 과거 데이터 로드 중...")
        days = self._min_bars * 2
        hist = yf.Ticker(self.ticker).history(period=f"{days}d", auto_adjust=True)
        closes = hist["Close"].dropna()
        if closes.empty:
            logger.warning(f"[초기화] yfinance 데이터 없음: {self.ticker}")
            return
        for price in closes.tail(self._min_bars):
            self._prices.append(float(price))
        logger.info(f"[초기화] {len(self._prices)}개 봉 로드 완료")

    # ── 장 세션 로깅 ───────────────────────────────────────────
    def _log_session_change(self, session: str):
        if session == self._last_session:
            return
        self._last_session = session
        label = session_label(session)
        clock = et_clock_str()
        if session == "market":
            logger.info(f"[장 개시] {label}  ({clock})  ▶ 자동매매 활성")
        elif session in ("pre_market", "after_hours"):
            logger.info(f"[{label}]  ({clock})  — 시간 외 거래 감시 중 (매매 중단)")
        elif session == "closed":
            logger.info(f"[장 종료] {label}  ({clock})")
        elif session == "holiday":
            logger.info(f"[휴장] {label}  ({clock})")

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

        if cur_rsi <= self.oversold and golden:
            return "BUY"
        if cur_rsi >= self.overbought and rsi_fall and dead:
            return "SELL"
        return "HOLD"

    # ── 주문 실행 ──────────────────────────────────────────────
    def _execute_buy(self, price: float):
        deposit = self.broker.get_deposit(self.account)
        budget  = int(deposit * self.buy_ratio)
        qty     = budget // int(price)

        if qty <= 0:
            logger.warning(f"[매수 불가] 잔고 부족: ${deposit:,.2f}")
            return

        logger.info(
            f"[매수 신호] {self.ticker} | ${price:,.2f} | "
            f"{qty}주 | 금액:${qty * price:,.2f}"
            + (" [모의]" if self.paper else "")
        )
        if not self.paper:
            self.broker.send_order(self.account, self.ticker, "BUY", qty)

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
            f"[매도 신호] {self.ticker} | ${price:,.2f} | "
            f"{qty}주 | 손익:${profit:+,.2f} ({profit_pct:+.2f}%)"
            + (" [모의]" if self.paper else "")
        )
        if not self.paper:
            self.broker.send_order(self.account, self.ticker, "SELL", qty)

        self._position   = False
        self._hold_qty   = 0
        self._hold_price = 0.0

    # ── 실시간 체결 콜백 ───────────────────────────────────────
    def _on_price(self, ticker: str, price: float):
        self._prices.append(price)

        session = get_session()
        self._log_session_change(session)

        ts    = datetime.now().strftime("%H:%M:%S")
        clock = et_clock_str()

        # ── 정규장 외 → 매매 중단 ─────────────────────────────
        if session != "market":
            label = session_label(session)
            logger.info(f"[{ts}] {ticker} ${price:.2f}  |  {label}  ({clock})")
            return

        # ── 정규장 → 신호 계산 & 매매 ─────────────────────────
        signal = self._compute_signal()

        rsi_val = ""
        if len(self._prices) >= self._min_bars:
            ps = pd.Series(list(self._prices))
            rsi_val = f"  RSI:{calculate_rsi(ps, self.rsi_period).iloc[-1]:.1f}"

        logger.info(
            f"[{ts}] {ticker} ${price:.2f}  |  신호:{signal}{rsi_val}  ({clock})"
        )

        if signal == self._last_signal:
            return
        self._last_signal = signal

        if signal == "BUY" and not self._position:
            self._execute_buy(price)
        elif signal == "SELL" and self._position:
            self._execute_sell(price)

    # ── 실행 진입점 ────────────────────────────────────────────
    def run(self):
        # stop_event/running을 먼저 초기화 — 이후 어느 시점에 stop()이
        # 호출되더라도 경합 없이 즉시 반영됨
        self._running = True
        self._stop_event.clear()

        logger.info("=" * 60)
        logger.info(f"  RSI+MACD 자동매매 시작")
        logger.info(f"  종목: {self.ticker} | 계좌: {self.account}")
        logger.info(f"  전략: RSI({self.rsi_period}) + MACD({self.macd_fast}/{self.macd_slow}/{self.macd_signal})")
        logger.info(f"  매수: RSI≤{self.oversold} + 골든크로스  |  매도: RSI≥{self.overbought} + 데드크로스")
        logger.info(f"  모드: {'모의매매 (주문 미전송)' if self.paper else '실제매매'}")
        logger.info(f"  현재 ET: {et_clock_str()}")
        logger.info("=" * 60)

        session = get_session()
        self._log_session_change(session)

        if not self.broker.login():
            logger.error("로그인 실패. 브로커 설정을 확인하세요.")
            return

        if not self._running:   # 로그인 중 stop() 호출 여부 확인
            return

        self._load_history()

        if not self._running:   # 히스토리 로드 중 stop() 호출 여부 확인
            return

        self.broker.subscribe_real(self.ticker, self._on_price)
        logger.info(f"{self.ticker} 실시간 감시 시작 (중지 버튼으로 종료)")

        try:
            while self._running:
                session = get_session()
                self._log_session_change(session)
                # 30초 대기 — stop() 호출 시 즉시 깨어남
                self._stop_event.wait(timeout=30)
                if self._stop_event.is_set():
                    break
        finally:
            self.broker.unsubscribe_real(self.ticker)
            logger.info("자동매매 종료")

    def stop(self):
        self._running = False
        self._stop_event.set()   # 대기 중인 sleep 즉시 해제
