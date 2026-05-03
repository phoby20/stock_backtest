"""
키움증권 OpenAPI+ 래퍼
- Windows 전용 (COM 기반 OCX)
- 실행 전 키움 OpenAPI+ 클라이언트 설치 및 로그인 필요
- PyQt5 이벤트 루프 위에서 동작
"""
import sys
import time
import logging
from collections import deque
from datetime import datetime
from typing import Callable, Optional

from PyQt5.QAxContainer import QAxWidget
from PyQt5.QtCore import QEventLoop

logger = logging.getLogger(__name__)

# 주문 타입
ORDER_BUY  = 1   # 신규매수
ORDER_SELL = 2   # 신규매도

# 호가 타입
PRICE_MARKET = "03"  # 시장가
PRICE_LIMIT  = "00"  # 지정가

# 실시간 FID
FID_CURRENT_PRICE = 10   # 현재가
FID_VOLUME        = 14   # 거래량
FID_TIME          = 20   # 체결시간


class KiwoomAPI(QAxWidget):
    def __init__(self):
        super().__init__()
        self.setControl("KHOPENAPI.KHOpenAPICtrl.1")

        self._login_loop: Optional[QEventLoop] = None
        self._tr_loop:    Optional[QEventLoop] = None
        self._tr_data:    dict = {}
        self._real_callbacks: dict[str, Callable] = {}

        # 이벤트 연결
        self.OnEventConnect.connect(self._on_connect)
        self.OnReceiveTrData.connect(self._on_receive_tr_data)
        self.OnReceiveRealData.connect(self._on_receive_real_data)
        self.OnReceiveChejanData.connect(self._on_receive_chejan)
        self.OnReceiveMsg.connect(self._on_receive_msg)

    # ── 로그인 ─────────────────────────────────────────────────
    def login(self) -> bool:
        """로그인 (블로킹). 성공 시 True 반환."""
        self._login_loop = QEventLoop()
        self.dynamicCall("CommConnect()")
        self._login_loop.exec_()
        state = self.dynamicCall("GetConnectState()")
        return state == 1

    def _on_connect(self, err_code: int):
        logger.info(f"[키움] 연결 결과: {err_code} ({'성공' if err_code == 0 else '실패'})")
        if self._login_loop:
            self._login_loop.exit()

    # ── 계좌 정보 ──────────────────────────────────────────────
    def get_account_list(self) -> list[str]:
        raw = self.dynamicCall("GetLoginInfo(QString)", "ACCLIST")
        return [a for a in raw.split(";") if a]

    def get_balance(self, account: str) -> dict:
        """예수금 및 보유 종목 조회"""
        self.dynamicCall("SetInputValue(QString, QString)", "계좌번호", account)
        self.dynamicCall("SetInputValue(QString, QString)", "비밀번호", "")
        self.dynamicCall("SetInputValue(QString, QString)", "비밀번호입력매체구분", "00")
        self.dynamicCall("SetInputValue(QString, QString)", "조회구분", "1")
        self._tr_request("opw00018", "계좌평가잔고내역요청", "0201")
        return self._tr_data.copy()

    def get_deposit(self, account: str) -> int:
        """주문 가능 예수금 조회"""
        self.dynamicCall("SetInputValue(QString, QString)", "계좌번호", account)
        self.dynamicCall("SetInputValue(QString, QString)", "비밀번호", "")
        self.dynamicCall("SetInputValue(QString, QString)", "비밀번호입력매체구분", "00")
        self.dynamicCall("SetInputValue(QString, QString)", "조회구분", "2")
        self._tr_request("opw00001", "예수금상세현황요청", "0101")
        deposit = self._tr_data.get("주문가능금액", "0")
        return int(deposit.replace(",", "")) if deposit else 0

    # ── 주가 데이터 조회 ───────────────────────────────────────
    def get_ohlcv(self, ticker: str, count: int = 100) -> list[dict]:
        """일봉 OHLCV 조회 (최근 count개)"""
        self.dynamicCall("SetInputValue(QString, QString)", "종목코드", ticker)
        self.dynamicCall("SetInputValue(QString, QString)", "기준일자",
                         datetime.today().strftime("%Y%m%d"))
        self.dynamicCall("SetInputValue(QString, QString)", "수정주가구분", "1")
        self._tr_request("opt10081", "주식일봉차트조회요청", "0301")
        return self._tr_data.get("ohlcv", [])

    def get_current_price(self, ticker: str) -> int:
        """현재가 단건 조회"""
        self.dynamicCall("SetInputValue(QString, QString)", "종목코드", ticker)
        self._tr_request("opt10001", "주식기본정보요청", "0101")
        price = self._tr_data.get("현재가", "0")
        return abs(int(price))

    # ── 주문 ───────────────────────────────────────────────────
    def send_order(
        self,
        account: str,
        ticker: str,
        order_type: int,
        quantity: int,
        price: int = 0,
        price_type: str = PRICE_MARKET,
    ) -> int:
        """
        주문 전송. 반환값 0 = 성공.
        price_type: PRICE_MARKET(시장가) / PRICE_LIMIT(지정가)
        """
        action = "매수" if order_type == ORDER_BUY else "매도"
        logger.info(f"[주문] {action} | {ticker} | {quantity}주 | 가격:{price if price else '시장가'}")
        result = self.dynamicCall(
            "SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)",
            [
                f"RSI_MACD_{action}",  # 주문명
                "0101",                # 화면번호
                account,
                order_type,
                ticker,
                quantity,
                price,
                price_type,
                "",                    # 원주문번호 (신규주문은 빈칸)
            ],
        )
        if result != 0:
            logger.error(f"[주문 실패] 오류코드: {result}")
        return result

    # ── 실시간 구독 ────────────────────────────────────────────
    def subscribe_real(self, ticker: str, callback: Callable[[str, float], None]):
        """실시간 체결 데이터 구독"""
        self._real_callbacks[ticker] = callback
        self.dynamicCall(
            "SetRealReg(QString, QString, QString, QString)",
            "9999",     # 화면번호
            ticker,
            f"{FID_CURRENT_PRICE};{FID_VOLUME};{FID_TIME}",
            "1",        # 1=기존 화면에 추가
        )
        logger.info(f"[실시간] {ticker} 구독 시작")

    def unsubscribe_real(self, ticker: str):
        self.dynamicCall("SetRealRemove(QString, QString)", "9999", ticker)
        self._real_callbacks.pop(ticker, None)

    def _on_receive_real_data(self, ticker: str, real_type: str, real_data: str):
        if real_type != "주식체결":
            return
        price_str = self.dynamicCall(
            "GetCommRealData(QString, int)", ticker, FID_CURRENT_PRICE
        )
        try:
            price = abs(float(price_str))
            if ticker in self._real_callbacks:
                self._real_callbacks[ticker](ticker, price)
        except ValueError:
            pass

    def _on_receive_chejan(self, s_gubun: str, n_item_cnt: int, s_fid_list: str):
        """체결/잔고 이벤트"""
        if s_gubun == "0":
            ticker = self.dynamicCall("GetChejanData(int)", 9001).strip()
            qty    = self.dynamicCall("GetChejanData(int)", 911).strip()
            price  = self.dynamicCall("GetChejanData(int)", 910).strip()
            logger.info(f"[체결] {ticker} | {qty}주 | {price}원")

    # ── TR 헬퍼 ───────────────────────────────────────────────
    def _tr_request(self, tr_code: str, rq_name: str, screen: str):
        self._tr_loop = QEventLoop()
        self.dynamicCall(
            "CommRqData(QString, QString, int, QString)",
            rq_name, tr_code, 0, screen,
        )
        self._tr_loop.exec_()

    def _on_receive_tr_data(
        self, screen: str, rq_name: str, tr_code: str,
        record: str, next_: str, *args
    ):
        self._tr_data = {}

        if tr_code == "opw00001":
            self._tr_data["주문가능금액"] = self.dynamicCall(
                "GetCommData(QString, QString, int, QString)",
                tr_code, rq_name, 0, "주문가능금액"
            ).strip()

        elif tr_code == "opw00018":
            rows = self.dynamicCall(
                "GetRepeatCnt(QString, QString)", tr_code, rq_name
            )
            holdings = []
            for i in range(rows):
                holdings.append({
                    "종목코드": self.dynamicCall("GetCommData(QString, QString, int, QString)",
                                             tr_code, rq_name, i, "종목코드").strip(),
                    "종목명":   self.dynamicCall("GetCommData(QString, QString, int, QString)",
                                             tr_code, rq_name, i, "종목명").strip(),
                    "보유수량": self.dynamicCall("GetCommData(QString, QString, int, QString)",
                                             tr_code, rq_name, i, "보유수량").strip(),
                    "현재가":   self.dynamicCall("GetCommData(QString, QString, int, QString)",
                                             tr_code, rq_name, i, "현재가").strip(),
                })
            self._tr_data["holdings"] = holdings

        elif tr_code == "opt10081":
            rows = self.dynamicCall(
                "GetRepeatCnt(QString, QString)", tr_code, rq_name
            )
            ohlcv = []
            for i in range(rows):
                ohlcv.append({
                    "date":   self.dynamicCall("GetCommData(QString, QString, int, QString)",
                                              tr_code, rq_name, i, "일자").strip(),
                    "open":   abs(int(self.dynamicCall("GetCommData(QString, QString, int, QString)",
                                                      tr_code, rq_name, i, "시가").strip() or 0)),
                    "high":   abs(int(self.dynamicCall("GetCommData(QString, QString, int, QString)",
                                                      tr_code, rq_name, i, "고가").strip() or 0)),
                    "low":    abs(int(self.dynamicCall("GetCommData(QString, QString, int, QString)",
                                                      tr_code, rq_name, i, "저가").strip() or 0)),
                    "close":  abs(int(self.dynamicCall("GetCommData(QString, QString, int, QString)",
                                                      tr_code, rq_name, i, "현재가").strip() or 0)),
                    "volume": abs(int(self.dynamicCall("GetCommData(QString, QString, int, QString)",
                                                      tr_code, rq_name, i, "거래량").strip() or 0)),
                })
            self._tr_data["ohlcv"] = ohlcv

        elif tr_code == "opt10001":
            self._tr_data["현재가"] = self.dynamicCall(
                "GetCommData(QString, QString, int, QString)",
                tr_code, rq_name, 0, "현재가"
            ).strip()

        if self._tr_loop:
            self._tr_loop.exit()

    def _on_receive_msg(self, screen: str, rq_name: str, tr_code: str, msg: str):
        logger.info(f"[키움 메시지] {msg}")
