import time
from datetime import datetime
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QSpinBox, QDoubleSpinBox,
    QPushButton, QTextEdit,
)
from gui.widgets import form_row, hline, make_scroll_sidebar


class MonitorWorker(QThread):
    tick    = pyqtSignal(str)
    stopped = pyqtSignal()

    def __init__(self, params):
        super().__init__()
        self.params   = params
        self._running = True

    def stop(self):
        self._running = False

    def run(self):
        from src.data.fetcher import fetch_historical_data, fetch_intraday_data
        from src.indicators.rsi import calculate_rsi
        from src.indicators.macd import calculate_macd, detect_golden_cross, detect_dead_cross

        p       = self.params
        base_df = fetch_historical_data(p["ticker"], period="60d")
        prices  = base_df["Close"].copy()

        while self._running:
            try:
                intraday     = fetch_intraday_data(p["ticker"], interval="5m", period="1d")
                latest_price = float(intraday["Close"].iloc[-1])
                latest_time  = intraday.index[-1]

                prices[latest_time] = latest_price
                prices = prices[~prices.index.duplicated(keep="last")].sort_index()

                rsi       = calculate_rsi(prices, period=p["rsi_period"])
                ml, sl, _ = calculate_macd(prices)
                cur_rsi   = float(rsi.iloc[-1])
                golden    = detect_golden_cross(ml, sl).iloc[-1]
                dead      = detect_dead_cross(ml, sl).iloc[-1]

                signal = "HOLD"
                if cur_rsi <= p["oversold"] and golden:
                    signal = "BUY"
                elif cur_rsi >= p["overbought"] and dead:
                    signal = "SELL"

                icon = {"BUY": "🟢", "SELL": "🔴", "HOLD": "⚪"}[signal]
                ts   = datetime.now().strftime("%H:%M:%S")
                msg  = (
                    f"[{ts}]  {p['ticker']}  "
                    f"현재가: {latest_price:,.2f}  |  "
                    f"RSI: {cur_rsi:.2f}  |  "
                    f"MACD: {'골든▲' if golden else '데드▼' if dead else '―'}  "
                    f"{icon} {signal}"
                )
                self.tick.emit(msg)

            except Exception as e:
                self.tick.emit(f"[오류] {e}")

            for _ in range(p["interval"]):
                if not self._running:
                    break
                time.sleep(1)

        self.stopped.emit()


class MonitorTab(QWidget):
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

        # 종목 설정
        sec1 = QLabel("종목 설정")
        sec1.setObjectName("sectionLabel")
        sv.addWidget(sec1)

        self.tickerEdit = QLineEdit("005930.KS")
        sv.addWidget(form_row("종목코드", self.tickerEdit))

        self.intervalSpin = QSpinBox()
        self.intervalSpin.setRange(10, 3600)
        self.intervalSpin.setValue(300)
        self.intervalSpin.setSuffix("  초")
        sv.addWidget(form_row("갱신 주기", self.intervalSpin))

        sv.addWidget(hline())

        # RSI · MACD 기준
        sec2 = QLabel("RSI · MACD 기준")
        sec2.setObjectName("sectionLabel")
        sv.addWidget(sec2)

        self.rsiSpin = QSpinBox()
        self.rsiSpin.setRange(2, 50)
        self.rsiSpin.setValue(14)
        sv.addWidget(form_row("RSI 기간", self.rsiSpin))

        self.oversoldSpin = QDoubleSpinBox()
        self.oversoldSpin.setRange(1, 49)
        self.oversoldSpin.setValue(30)
        self.oversoldSpin.setSuffix("  (≤ 매수)")
        sv.addWidget(form_row("과매도 기준", self.oversoldSpin))

        self.overboughtSpin = QDoubleSpinBox()
        self.overboughtSpin.setRange(51, 99)
        self.overboughtSpin.setValue(70)
        self.overboughtSpin.setSuffix("  (≥ 매도)")
        sv.addWidget(form_row("과매수 기준", self.overboughtSpin))

        sv.addStretch()
        sv.addWidget(hline())

        self.startBtn = QPushButton("▶   감시 시작")
        self.startBtn.setObjectName("primaryBtn")
        self.startBtn.setMinimumHeight(38)
        self.startBtn.clicked.connect(self._start)
        sv.addWidget(self.startBtn)

        self.stopBtn = QPushButton("■   감시 중지")
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

        info = QLabel("실시간으로 RSI · MACD 신호를 감시합니다.\n🟢 매수 신호  /  🔴 매도 신호  /  ⚪ 대기")
        info.setObjectName("infoLabel")
        info.setWordWrap(True)
        mv.addWidget(info)

        log_label = QLabel("실시간 로그")
        log_label.setObjectName("sectionLabel")
        mv.addWidget(log_label)

        self.logEdit = QTextEdit()
        self.logEdit.setReadOnly(True)
        mv.addWidget(self.logEdit)

        root.addWidget(main)

    def _start(self):
        params = {
            "ticker":     self.tickerEdit.text().strip(),
            "interval":   self.intervalSpin.value(),
            "rsi_period": self.rsiSpin.value(),
            "oversold":   self.oversoldSpin.value(),
            "overbought": self.overboughtSpin.value(),
        }
        self.logEdit.clear()
        self._log(f"감시 시작  |  {params['ticker']}  |  주기: {params['interval']}초")
        self._worker = MonitorWorker(params)
        self._worker.tick.connect(self._log)
        self._worker.stopped.connect(self._on_stopped)
        self._worker.start()
        self.startBtn.setEnabled(False)
        self.stopBtn.setEnabled(True)

    def _stop(self):
        if self._worker:
            self._worker.stop()
        self.stopBtn.setEnabled(False)

    def _on_stopped(self):
        self._log("감시 종료.")
        self.startBtn.setEnabled(True)

    def _log(self, msg):
        self.logEdit.append(msg)
