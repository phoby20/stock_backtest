import sys
import logging
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QSpinBox, QDoubleSpinBox,
    QPushButton, QTextEdit, QCheckBox,
)
from gui.widgets import form_row, hline, make_scroll_sidebar


class QtLogHandler(logging.Handler):
    def __init__(self, signal):
        super().__init__()
        self._signal = signal

    def emit(self, record):
        self._signal.emit(self.format(record))


class TradeWorker(QThread):
    log     = pyqtSignal(str)
    stopped = pyqtSignal()

    def __init__(self, params):
        super().__init__()
        self.params  = params
        self._trader = None

    def stop(self):
        if self._trader and self._trader.api:
            self._trader.api.unsubscribe_real(self.params["ticker"])

    def run(self):
        try:
            from src.trading.live_trader import LiveTrader
            p = self.params
            handler = QtLogHandler(self.log)
            handler.setFormatter(logging.Formatter("%(asctime)s  %(message)s", "%H:%M:%S"))
            logging.getLogger().addHandler(handler)
            self._trader = LiveTrader(
                ticker=p["ticker"], account=p["account"],
                rsi_period=p["rsi_period"],
                oversold=p["oversold"], overbought=p["overbought"],
                macd_fast=p["macd_fast"], macd_slow=p["macd_slow"],
                macd_signal=p["macd_signal"],
                buy_ratio=p["buy_ratio"], paper=p["paper"],
            )
            self._trader.run()
        except Exception as e:
            self.log.emit(f"[오류] {e}")
        finally:
            self.stopped.emit()


class TradeTab(QWidget):
    def __init__(self):
        super().__init__()
        self._worker = None
        self._setup_ui()

    def _setup_ui(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── 사이드바 내부 ─────────────────────────────────────
        inner = QWidget()
        inner.setStyleSheet("background:#161b22;")
        sv = QVBoxLayout(inner)
        sv.setContentsMargins(16, 16, 16, 16)
        sv.setSpacing(10)

        # Windows 경고
        if sys.platform != "win32":
            warn = QLabel("⚠️  키움 OpenAPI+는 Windows 전용입니다.\n이 환경에서는 UI 확인만 가능합니다.")
            warn.setObjectName("warningLabel")
            warn.setWordWrap(True)
            sv.addWidget(warn)

        # 계좌 · 종목
        sec1 = QLabel("계좌 · 종목")
        sec1.setObjectName("sectionLabel")
        sv.addWidget(sec1)

        self.tickerEdit = QLineEdit("005930")
        sv.addWidget(form_row("종목코드", self.tickerEdit))

        self.accountEdit = QLineEdit()
        self.accountEdit.setPlaceholderText("예: 1234567890")
        sv.addWidget(form_row("계좌번호", self.accountEdit))

        self.buyRatioSpin = QDoubleSpinBox()
        self.buyRatioSpin.setRange(0.01, 1.0)
        self.buyRatioSpin.setValue(1.0)
        self.buyRatioSpin.setSingleStep(0.1)
        self.buyRatioSpin.setSuffix("  (전액=1.0)")
        sv.addWidget(form_row("매수 비율", self.buyRatioSpin))

        self.paperCheck = QCheckBox("모의매매  (실제 주문 미전송)")
        self.paperCheck.setChecked(True)
        sv.addWidget(self.paperCheck)

        sv.addWidget(hline())

        # RSI + MACD 파라미터
        sec2 = QLabel("RSI + MACD 파라미터")
        sec2.setObjectName("sectionLabel")
        sv.addWidget(sec2)

        specs = [
            ("RSI 기간",    "rsiSpin",       2,  50,  14),
            ("매수 기준 ≤", "buyRsiSpin",    1,  49,  30),
            ("매도 기준 ≥", "sellRsiSpin",  51,  99,  70),
            ("MACD 단기",   "macdFastSpin",  2, 100,  12),
            ("MACD 장기",   "macdSlowSpin",  2, 200,  26),
            ("시그널",      "macdSigSpin",   2,  50,   9),
        ]
        for label, attr, lo, hi, val in specs:
            sp = QSpinBox()
            sp.setRange(lo, hi)
            sp.setValue(val)
            setattr(self, attr, sp)
            sv.addWidget(form_row(label, sp))

        sv.addStretch()
        sv.addWidget(hline())

        self.startBtn = QPushButton("▶   자동매매 시작")
        self.startBtn.setObjectName("primaryBtn")
        self.startBtn.setMinimumHeight(38)
        self.startBtn.clicked.connect(self._start)
        sv.addWidget(self.startBtn)

        self.stopBtn = QPushButton("■   자동매매 중지")
        self.stopBtn.setObjectName("stopBtn")
        self.stopBtn.setMinimumHeight(36)
        self.stopBtn.setEnabled(False)
        self.stopBtn.clicked.connect(self._stop)
        sv.addWidget(self.stopBtn)

        root.addWidget(make_scroll_sidebar(inner))

        # ── 메인 영역 ─────────────────────────────────────────
        main = QWidget()
        mv = QVBoxLayout(main)
        mv.setContentsMargins(20, 16, 20, 16)
        mv.setSpacing(10)

        notice = QLabel(
            "⚠️  실제매매 전 반드시 모의매매로 충분히 검증하세요.\n"
            "투자 손실에 대한 책임은 본인에게 있습니다."
        )
        notice.setObjectName("warningLabel")
        notice.setWordWrap(True)
        mv.addWidget(notice)

        log_label = QLabel("거래 로그")
        log_label.setObjectName("sectionLabel")
        mv.addWidget(log_label)

        self.logEdit = QTextEdit()
        self.logEdit.setReadOnly(True)
        mv.addWidget(self.logEdit)

        root.addWidget(main)

    def _start(self):
        if not self.accountEdit.text().strip():
            self._log("계좌번호를 입력하세요.")
            return
        params = {
            "ticker":      self.tickerEdit.text().strip(),
            "account":     self.accountEdit.text().strip(),
            "rsi_period":  self.rsiSpin.value(),
            "oversold":    self.buyRsiSpin.value(),
            "overbought":  self.sellRsiSpin.value(),
            "macd_fast":   self.macdFastSpin.value(),
            "macd_slow":   self.macdSlowSpin.value(),
            "macd_signal": self.macdSigSpin.value(),
            "buy_ratio":   self.buyRatioSpin.value(),
            "paper":       self.paperCheck.isChecked(),
        }
        mode = "모의매매" if params["paper"] else "⚠️ 실제매매"
        self.logEdit.clear()
        self._log(f"[{mode}]  {params['ticker']}  자동매매 시작…")
        self._worker = TradeWorker(params)
        self._worker.log.connect(self._log)
        self._worker.stopped.connect(self._on_stopped)
        self._worker.start()
        self.startBtn.setEnabled(False)
        self.stopBtn.setEnabled(True)

    def _stop(self):
        if self._worker:
            self._worker.stop()
        self.stopBtn.setEnabled(False)

    def _on_stopped(self):
        self._log("자동매매 종료.")
        self.startBtn.setEnabled(True)

    def _log(self, msg):
        self.logEdit.append(msg)
