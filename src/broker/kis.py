"""
한국투자증권 OpenAPI — 해외주식(미국) 전용
- 지원 거래소: NASD(나스닥), NYSE(뉴욕), AMEX(아멕스)
- 현재가 폴링: yfinance 1분봉 (paper/real 서버 제한 없음)
- 주문 / 잔고: KIS REST API
- 모의투자 URL : https://openapivts.koreainvestment.com:29443
- 실거래 URL   : https://openapi.koreainvestment.com:9443
"""
import json
import logging
import os
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Callable, Optional

import requests

logger = logging.getLogger(__name__)

ORDER_BUY  = "BUY"
ORDER_SELL = "SELL"

# 거래소 코드: order body(4자) → price inquiry(3자)
_EXCD_MAP = {"NASD": "NAS", "NYSE": "NYS", "AMEX": "AMS"}

# 토큰 파일 위치 (config_store 와 동일 디렉터리)
_TOKEN_FILE = Path.home() / ".rsi_macd_trader" / "kis_tokens.json"


class KISAPI:
    REAL_BASE  = "https://openapi.koreainvestment.com:9443"
    PAPER_BASE = "https://openapivts.koreainvestment.com:29443"

    # 프로세스 내 공유 메모리 캐시: (app_key, base_url) → (token, expires)
    _TOKEN_CACHE: dict = {}

    def __init__(self, app_key: str, app_secret: str,
                 paper: bool = True, exchange: str = "NASD"):
        self.app_key    = app_key.strip()
        self.app_secret = app_secret.strip()
        self.paper      = paper
        self.base_url   = self.PAPER_BASE if paper else self.REAL_BASE
        self.exchange   = exchange
        self._excd      = _EXCD_MAP.get(exchange, "NAS")

        self._access_token:  Optional[str]      = None
        self._token_expires: Optional[datetime] = None
        self._real_callbacks: dict[str, Callable] = {}
        self._poll_thread:   Optional[threading.Thread] = None
        self._running    = False
        self._stop_event = threading.Event()

        # 인스턴스 생성 시 캐시에서 유효 토큰 복원
        self._restore_token()

    # ── 토큰 캐시 ──────────────────────────────────────────────────

    def _cache_key(self) -> tuple:
        return (self.app_key, self.base_url)

    def _restore_token(self):
        """메모리 캐시 → 파일 캐시 순으로 유효 토큰을 복원."""
        # 1) 프로세스 내 메모리 캐시
        cached = KISAPI._TOKEN_CACHE.get(self._cache_key())
        if cached:
            token, expires = cached
            if datetime.now() < expires:
                self._access_token  = token
                self._token_expires = expires
                return

        # 2) 파일 캐시 (앱 재시작 후에도 재사용)
        try:
            if _TOKEN_FILE.exists():
                data  = json.loads(_TOKEN_FILE.read_text(encoding="utf-8"))
                entry = data.get(self._file_cache_key())
                if entry:
                    expires = datetime.fromisoformat(entry["expires"])
                    if datetime.now() < expires:
                        self._access_token  = entry["token"]
                        self._token_expires = expires
                        # 메모리 캐시에도 올려둠
                        KISAPI._TOKEN_CACHE[self._cache_key()] = (
                            self._access_token, self._token_expires
                        )
        except Exception:
            pass

    def _file_cache_key(self) -> str:
        return f"{self.app_key[:20]}_{'paper' if self.paper else 'real'}"

    def _persist_token(self):
        """유효 토큰을 메모리 캐시와 파일에 저장."""
        KISAPI._TOKEN_CACHE[self._cache_key()] = (
            self._access_token, self._token_expires
        )
        try:
            _TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
            existing: dict = {}
            if _TOKEN_FILE.exists():
                try:
                    existing = json.loads(_TOKEN_FILE.read_text(encoding="utf-8"))
                except Exception:
                    pass
            existing[self._file_cache_key()] = {
                "token":   self._access_token,
                "expires": self._token_expires.isoformat(),
            }
            _TOKEN_FILE.write_text(
                json.dumps(existing, ensure_ascii=False), encoding="utf-8"
            )
            os.chmod(_TOKEN_FILE, 0o600)
        except Exception:
            pass

    # ── 인증 ──────────────────────────────────────────────────────

    def login(self) -> bool:
        # 유효 토큰이 있으면 새로 발급하지 않음 (분당 1회 제한 회피)
        if self._access_token and self._token_expires and datetime.now() < self._token_expires:
            mode = "모의투자" if self.paper else "실거래"
            logger.info(f"[KIS] 토큰 재사용 ({mode} / {self.exchange})")
            return True

        ok = self._refresh_token()
        mode = "모의투자" if self.paper else "실거래"
        if ok:
            logger.info(f"[KIS] 로그인 성공 ({mode} / {self.exchange})")
        else:
            logger.error("[KIS] 로그인 실패 — App Key / App Secret을 확인하세요.")
        return ok

    def _refresh_token(self) -> bool:
        try:
            resp = requests.post(
                f"{self.base_url}/oauth2/tokenP",
                json={
                    "grant_type": "client_credentials",
                    "appkey":     self.app_key,
                    "appsecret":  self.app_secret,
                },
                timeout=10,
            )
            data  = resp.json()
            token = data.get("access_token")
            if not token:
                err = (
                    data.get("error_description")
                    or data.get("msg1")
                    or str(data)
                )
                logger.error(f"[KIS] 토큰 발급 실패: {err}")
                return False
            self._access_token  = token
            expires_in          = int(data.get("expires_in", 86400))
            self._token_expires = datetime.now() + timedelta(seconds=expires_in - 300)
            self._persist_token()   # 메모리 + 파일 캐시 저장
            return True
        except Exception as e:
            logger.error(f"[KIS] 토큰 요청 오류: {e}")
            return False

    def _headers(self, tr_id: str, base: Optional[str] = None) -> dict:
        if not self._access_token or datetime.now() >= self._token_expires:
            self._refresh_token()
        return {
            "Content-Type":  "application/json",
            "Authorization": f"Bearer {self._access_token}",
            "appkey":        self.app_key,
            "appsecret":     self.app_secret,
            "tr_id":         tr_id,
            "custtype":      "P",
        }

    @staticmethod
    def _parse_account(account: str) -> tuple[str, str]:
        """'12345678-01' 또는 '1234567801' → ('12345678', '01')"""
        account = account.strip()
        if "-" in account:
            parts = account.split("-", 1)
            return parts[0].strip(), parts[1].strip()
        if len(account) >= 10:
            return account[:8], account[8:10]
        return account, "01"

    # ── 잔고 ──────────────────────────────────────────────────────
    def get_deposit(self, account: str) -> float:
        """해외주식 USD 주문가능 예수금 조회"""
        cano, prod = self._parse_account(account)
        tr_id = "VTTS3012R" if self.paper else "TTTS3012R"
        try:
            resp = requests.get(
                f"{self.base_url}/uapi/overseas-stock/v1/trading/inquire-balance",
                headers=self._headers(tr_id),
                params={
                    "CANO":           cano,
                    "ACNT_PRDT_CD":   prod,
                    "OVRS_EXCG_CD":   self.exchange,
                    "TR_CRCY_CD":     "USD",
                    "CTX_AREA_FK200": "",
                    "CTX_AREA_NK200": "",
                },
                timeout=10,
            )
            out2 = resp.json().get("output2", {})
            val = out2.get("frcr_dncl_amt2") or out2.get("frcr_buy_amt_smtl1", "0")
            return float(val or 0)
        except Exception as e:
            logger.error(f"[KIS] 해외 잔고 조회 실패: {e}")
            return 0.0

    # ── 현재가 (주문 시 지정가 산출용) ────────────────────────────
    def get_current_price(self, ticker: str) -> float:
        """KIS 해외주식 현재가 (실서버 기준)"""
        try:
            resp = requests.get(
                f"{self.REAL_BASE}/uapi/overseas-price/v1/quotations/price",
                headers=self._headers("HHDFS00000300"),
                params={"AUTH": "", "EXCD": self._excd, "SYMB": ticker},
                timeout=10,
            )
            return float(resp.json().get("output", {}).get("last", 0) or 0)
        except Exception as e:
            logger.error(f"[KIS] 해외 현재가 조회 실패: {e}")
            return 0.0

    # ── 주문 ──────────────────────────────────────────────────────
    def send_order(self, account: str, ticker: str,
                   order_type: str, quantity: int) -> bool:
        """
        해외주식 지정가 주문 (현재가로 즉시 체결 유도).
        미국 주식은 시장가 주문 코드가 없어 현재가 지정가로 대체.
        """
        cano, prod = self._parse_account(account)
        if order_type == ORDER_BUY:
            tr_id = "VTTT1002U" if self.paper else "TTTT1002U"
        else:
            tr_id = "VTTT1006U" if self.paper else "TTTT1006U"

        price = self.get_current_price(ticker)
        if price <= 0:
            logger.error("[KIS] 현재가 조회 실패 → 주문 취소")
            return False

        body = {
            "CANO":          cano,
            "ACNT_PRDT_CD":  prod,
            "OVRS_EXCG_CD":  self.exchange,
            "PDNO":          ticker,
            "ORD_DVSN":      "00",
            "ORD_QTY":       str(quantity),
            "OVRS_ORD_UNPR": f"{price:.2f}",
        }
        try:
            resp = requests.post(
                f"{self.base_url}/uapi/overseas-stock/v1/trading/order",
                headers=self._headers(tr_id),
                json=body,
                timeout=10,
            )
            data  = resp.json()
            ok    = data.get("rt_cd") == "0"
            label = "매수" if order_type == ORDER_BUY else "매도"
            if ok:
                logger.info(f"[KIS] {label} 주문 성공: {ticker} {quantity}주 @${price:.2f}")
            else:
                logger.error(f"[KIS] {label} 주문 실패: {data.get('msg1', data)}")
            return ok
        except Exception as e:
            logger.error(f"[KIS] 주문 오류: {e}")
            return False

    # ── 실시간 폴링 (yfinance 1분봉) ─────────────────────────────
    def subscribe_real(self, ticker: str,
                       callback: Callable[[str, float], None]):
        self._real_callbacks[ticker] = callback
        if not self._running:
            self._running = True
            self._stop_event.clear()
            self._poll_thread = threading.Thread(
                target=self._poll_loop, daemon=True, name="KIS-poll"
            )
            self._poll_thread.start()
        logger.info(f"[KIS] {ticker} 실시간 구독 시작 (yfinance 1분 폴링)")

    def unsubscribe_real(self, ticker: str):
        self._real_callbacks.pop(ticker, None)
        if not self._real_callbacks:
            self._running = False
            self._stop_event.set()
        logger.info(f"[KIS] {ticker} 실시간 구독 해제")

    def _poll_loop(self):
        import yfinance as yf
        while self._running:
            for ticker, cb in list(self._real_callbacks.items()):
                try:
                    hist = yf.Ticker(ticker).history(period="1d", interval="1m")
                    if not hist.empty:
                        price = float(hist["Close"].iloc[-1])
                        if price > 0:
                            cb(ticker, price)
                except Exception:
                    pass
            # 60초 대기 — stop 시 즉시 깨어남
            self._stop_event.wait(timeout=60)
