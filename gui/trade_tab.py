import sys
import logging
from datetime import datetime
from PyQt5.QtCore import QThread, QTimer, pyqtSignal
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QSpinBox, QDoubleSpinBox,
    QPushButton, QTextEdit, QCheckBox, QComboBox,
    QStackedWidget, QFrame, QAbstractSpinBox,
)
from gui.widgets import form_row, hline, make_scroll_sidebar
from src.utils.config_store import load_secret, save_value, load_value


class QtLogHandler(logging.Handler):
    def __init__(self, signal):
        super().__init__()
        self._signal = signal

    def emit(self, record):
        try:
            self._signal.emit(self.format(record))
        except RuntimeError:
            pass  # 수신자 QObject가 이미 삭제됨 — 무시


class TradeWorker(QThread):
    log     = pyqtSignal(str)
    stopped = pyqtSignal()

    def __init__(self, params):
        super().__init__()
        self.params  = params
        self._trader = None

    def stop(self):
        if self._trader:
            self._trader.stop()

    def run(self):
        # handler은 항상 finally에서 제거되어야 하므로 try 블록 밖에서 생성
        _logger = logging.getLogger()
        handler = QtLogHandler(self.log)
        handler.setFormatter(logging.Formatter("%(asctime)s  %(message)s", "%H:%M:%S"))
        _logger.addHandler(handler)
        try:
            from src.trading.live_trader import LiveTrader
            from src.utils.config_store import load_secret
            p = self.params

            # ── 브로커 생성 (인증 정보는 config_store에서 읽음) ──
            broker_type = p.get("broker_type", "kiwoom")
            self.log.emit(f"  브로커 초기화 중… ({broker_type.upper()})")
            if broker_type == "kis":
                from src.broker.kis import KISAPI
                broker = KISAPI(
                    app_key    = load_secret("kis_app_key"),
                    app_secret = load_secret("kis_app_secret"),
                    paper      = p["paper"],
                    exchange   = p.get("kis_exchange", "NASD"),
                )
                account = load_secret("kis_account")
            else:
                if sys.platform != "win32":
                    self.log.emit("[오류] 키움증권 OpenAPI+는 Windows에서만 동작합니다.")
                    return  # finally가 handler 제거 + stopped 발신 처리
                from src.broker.kiwoom import KiwoomAPI
                broker  = KiwoomAPI()
                account = load_secret("kiwoom_account")

            self._trader = LiveTrader(
                broker      = broker,
                ticker      = p["ticker"],
                account     = account,
                rsi_period  = p["rsi_period"],
                oversold    = p["oversold"],
                overbought  = p["overbought"],
                macd_fast   = p["macd_fast"],
                macd_slow   = p["macd_slow"],
                macd_signal = p["macd_signal"],
                buy_ratio   = p["buy_ratio"],
                paper       = p["paper"],
            )
            self._trader.run()
        except Exception as e:
            self.log.emit(f"[오류] {e}")
        finally:
            _logger.removeHandler(handler)   # 누적 방지: 반드시 제거
            self.stopped.emit()


# ── 브로커별 입력 패널 (인증 정보는 설정 탭에서 관리) ──────────────

class _KiwoomPanel(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        if sys.platform != "win32":
            warn = QLabel("⚠️  키움 OpenAPI+는 Windows 전용입니다.\n이 환경에서는 UI 확인만 가능합니다.")
            warn.setObjectName("warningLabel")
            warn.setWordWrap(True)
            layout.addWidget(warn)

        hint = QLabel("계좌번호는 설정 탭에서 입력하세요.")
        hint.setStyleSheet("color:#8b949e; font-size:11px; background:transparent;")
        layout.addWidget(hint)

    def validate(self) -> str:
        if not load_secret("kiwoom_account"):
            return "설정 탭에서 키움증권 계좌번호를 먼저 입력하세요."
        return ""

    def extra_params(self) -> dict:
        return {}


class _KISPanel(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        hint = QLabel("App Key · App Secret · 계좌번호는 설정 탭에서 입력하세요.")
        hint.setStyleSheet("color:#8b949e; font-size:11px; background:transparent;")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        self.exchangeCombo = QComboBox()
        self.exchangeCombo.addItems(["NASD  (나스닥)", "NYSE  (뉴욕)", "AMEX  (아멕스)"])
        layout.addWidget(form_row("거래소", self.exchangeCombo))

        self.paperCheck = QCheckBox("모의투자  (한투 OpenAPI 모의 서버)")
        self.paperCheck.setChecked(True)
        layout.addWidget(self.paperCheck)

    def exchange(self) -> str:
        return self.exchangeCombo.currentText().split()[0]

    def validate(self) -> str:
        missing = []
        if not load_secret("kis_app_key"):
            missing.append("App Key")
        if not load_secret("kis_app_secret"):
            missing.append("App Secret")
        if not load_secret("kis_account"):
            missing.append("계좌번호")
        if missing:
            return f"설정 탭에서 KIS {' · '.join(missing)}를 먼저 입력하세요."
        return ""

    def extra_params(self) -> dict:
        return {"kis_exchange": self.exchange()}

    def is_paper(self) -> bool:
        return self.paperCheck.isChecked()


# ── 메인 탭 ──────────────────────────────────────────────────────

class TradeTab(QWidget):
    def __init__(self):
        super().__init__()
        self._worker           = None
        self._finishing_workers: set = set()  # finished 전까지 Python ref 유지
        self._blink_on      = False
        self._start_time    = None
        self._blink_timer   = None
        self._elapsed_timer = None
        self._setup_ui()
        self._load_settings()
        self._connect_autosave()

    def _setup_ui(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── 사이드바 내부 ─────────────────────────────────────
        inner = QWidget()
        inner.setStyleSheet("background:#161b22;")
        sv = QVBoxLayout(inner)
        sv.setContentsMargins(16, 16, 16, 16)
        sv.setSpacing(14)

        # 브로커 선택
        broker_sec = QLabel("브로커 선택")
        broker_sec.setObjectName("sectionLabel")
        sv.addWidget(broker_sec)

        self.brokerCombo = QComboBox()
        self.brokerCombo.addItems(["키움증권 (Kiwoom)", "한국투자증권 (KIS)"])
        self.brokerCombo.currentIndexChanged.connect(self._on_broker_changed)
        sv.addWidget(self.brokerCombo)

        sv.addWidget(hline())

        # 브로커별 패널 (QStackedWidget)
        self.brokerStack = QStackedWidget()
        self._kiwoomPanel = _KiwoomPanel()
        self._kisPanel    = _KISPanel()
        self.brokerStack.addWidget(self._kiwoomPanel)   # index 0
        self.brokerStack.addWidget(self._kisPanel)      # index 1
        sv.addWidget(self.brokerStack)

        sv.addWidget(hline())

        # 공통: 종목 · 비율
        sec1 = QLabel("종목 · 주문 설정")
        sec1.setObjectName("sectionLabel")
        sv.addWidget(sec1)

        self.tickerEdit = QLineEdit("SOXL")
        self.tickerEdit.setPlaceholderText("예: SOXL, AAPL, TSLA")
        sv.addWidget(form_row("티커", self.tickerEdit))

        self.buyRatioSpin = QDoubleSpinBox()
        self.buyRatioSpin.setRange(0.01, 1.0)
        self.buyRatioSpin.setValue(1.0)
        self.buyRatioSpin.setSingleStep(0.1)
        self.buyRatioSpin.setSuffix("  (전액=1.0)")
        self.buyRatioSpin.setButtonSymbols(QAbstractSpinBox.PlusMinus)
        sv.addWidget(form_row("매수 비율", self.buyRatioSpin))

        # 키움증권 전용 모의매매 체크 (KIS는 패널 내부에 있음)
        self.kiwoomPaperCheck = QCheckBox("모의매매  (실제 주문 미전송)")
        self.kiwoomPaperCheck.setChecked(True)
        sv.addWidget(self.kiwoomPaperCheck)

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
            sp.setButtonSymbols(QAbstractSpinBox.PlusMinus)
            setattr(self, attr, sp)
            sv.addWidget(form_row(label, sp))

        sv.addStretch()
        sv.addWidget(hline())

        # 실행 상태 표시
        run_row = QHBoxLayout()
        run_row.setSpacing(6)
        self._dotLabel = QLabel("●")
        self._dotLabel.setStyleSheet("color:#3d444d; font-size:16px;")
        self._stateLabel = QLabel("대기 중")
        self._stateLabel.setStyleSheet("color:#8b949e; font-size:12px;")
        self._elapsedLabel = QLabel("")
        self._elapsedLabel.setStyleSheet("color:#8b949e; font-size:11px;")
        run_row.addWidget(self._dotLabel)
        run_row.addWidget(self._stateLabel)
        run_row.addStretch()
        run_row.addWidget(self._elapsedLabel)
        sv.addLayout(run_row)

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

        # ── NYSE 장 상태 패널 ─────────────────────────────────
        status_frame = QFrame()
        status_frame.setObjectName("statusFrame")
        status_frame.setStyleSheet(
            "QFrame#statusFrame {"
            "  background:#161b22; border:1px solid #30363d;"
            "  border-radius:6px; padding:8px;"
            "}"
        )
        sf_layout = QHBoxLayout(status_frame)
        sf_layout.setContentsMargins(12, 8, 12, 8)
        sf_layout.setSpacing(24)

        session_title = QLabel("NYSE 장 상태")
        session_title.setStyleSheet("color:#8b949e; font-size:12px;")
        sf_layout.addWidget(session_title)

        self.sessionLabel = QLabel("—")
        self.sessionLabel.setStyleSheet("font-weight:bold; font-size:13px;")
        sf_layout.addWidget(self.sessionLabel)

        sf_layout.addStretch()

        et_title = QLabel("ET 현재 시각")
        et_title.setStyleSheet("color:#8b949e; font-size:12px;")
        sf_layout.addWidget(et_title)

        self.etClockLabel = QLabel("—")
        self.etClockLabel.setStyleSheet("color:#c9d1d9; font-size:13px;")
        sf_layout.addWidget(self.etClockLabel)

        mv.addWidget(status_frame)

        # 30초마다 장 상태 갱신
        self._status_timer = QTimer(self)
        self._status_timer.timeout.connect(self._update_market_status)
        self._status_timer.start(30_000)
        self._update_market_status()

        log_label = QLabel("거래 로그")
        log_label.setObjectName("sectionLabel")
        mv.addWidget(log_label)

        self.logEdit = QTextEdit()
        self.logEdit.setReadOnly(True)
        mv.addWidget(self.logEdit)

        root.addWidget(main)

        # 초기 상태 동기화
        self._on_broker_changed(0)

    def _on_broker_changed(self, index: int):
        self.brokerStack.setCurrentIndex(index)
        # 키움: 공통 모의매매 체크 표시 / KIS: 숨기기 (KIS 패널 내부에 있음)
        self.kiwoomPaperCheck.setVisible(index == 0)

    # ── 설정 저장 / 불러오기 ──────────────────────────────────────

    def _load_settings(self):
        # 브로커 선택
        self.brokerCombo.setCurrentIndex(int(load_value("broker_idx", 0)))
        # KIS 설정
        self._kisPanel.exchangeCombo.setCurrentIndex(int(load_value("kis_exchange_idx", 0)))
        self._kisPanel.paperCheck.setChecked(bool(load_value("kis_paper", True)))
        # 키움 설정
        self.kiwoomPaperCheck.setChecked(bool(load_value("kiwoom_paper", True)))
        # 공통
        self.tickerEdit.setText(str(load_value("ticker", "SOXL")))
        self.buyRatioSpin.setValue(float(load_value("buy_ratio", 1.0)))
        # RSI / MACD 파라미터
        self.rsiSpin.setValue(int(load_value("rsi_period", 14)))
        self.buyRsiSpin.setValue(int(load_value("rsi_oversold", 30)))
        self.sellRsiSpin.setValue(int(load_value("rsi_overbought", 70)))
        self.macdFastSpin.setValue(int(load_value("macd_fast", 12)))
        self.macdSlowSpin.setValue(int(load_value("macd_slow", 26)))
        self.macdSigSpin.setValue(int(load_value("macd_signal", 9)))

    def _save_settings(self):
        """인증 정보 제외한 일반 설정만 저장 (인증 정보는 설정 탭에서 관리)."""
        save_value("broker_idx",       self.brokerCombo.currentIndex())
        save_value("kis_exchange_idx", self._kisPanel.exchangeCombo.currentIndex())
        save_value("kis_paper",        self._kisPanel.paperCheck.isChecked())
        save_value("kiwoom_paper",     self.kiwoomPaperCheck.isChecked())
        save_value("ticker",           self.tickerEdit.text().strip())
        save_value("buy_ratio",        self.buyRatioSpin.value())
        save_value("rsi_period",       self.rsiSpin.value())
        save_value("rsi_oversold",     self.buyRsiSpin.value())
        save_value("rsi_overbought",   self.sellRsiSpin.value())
        save_value("macd_fast",        self.macdFastSpin.value())
        save_value("macd_slow",        self.macdSlowSpin.value())
        save_value("macd_signal",      self.macdSigSpin.value())

    def _connect_autosave(self):
        self.brokerCombo.currentIndexChanged.connect(self._save_settings)
        self._kisPanel.exchangeCombo.currentIndexChanged.connect(self._save_settings)
        self._kisPanel.paperCheck.stateChanged.connect(self._save_settings)
        self.kiwoomPaperCheck.stateChanged.connect(self._save_settings)
        self.tickerEdit.editingFinished.connect(self._save_settings)

    def _update_market_status(self):
        try:
            from src.utils.market_hours import get_session, session_label, session_color, et_clock_str
            session = get_session()
            self.sessionLabel.setText(session_label(session))
            self.sessionLabel.setStyleSheet(
                f"font-weight:bold; font-size:13px; color:{session_color(session)};"
            )
            self.etClockLabel.setText(et_clock_str())
        except Exception:
            pass

    # ── 실행 인디케이터 ───────────────────────────────────────────

    def _start_indicator(self):
        import time as _time
        self._start_time = _time.time()
        self._blink_on = True

        self._blink_timer = QTimer(self)
        self._blink_timer.timeout.connect(self._blink)
        self._blink_timer.start(600)          # 0.6초마다 점멸

        self._elapsed_timer = QTimer(self)
        self._elapsed_timer.timeout.connect(self._update_elapsed)
        self._elapsed_timer.start(1_000)      # 1초마다 경과 시간 갱신
        self._update_elapsed()

    def _stop_indicator(self):
        if self._blink_timer:
            self._blink_timer.stop()
            self._blink_timer = None
        if self._elapsed_timer:
            self._elapsed_timer.stop()
            self._elapsed_timer = None
        self._dotLabel.setStyleSheet("color:#3d444d; font-size:16px;")
        self._stateLabel.setText("대기 중")
        self._stateLabel.setStyleSheet("color:#8b949e; font-size:12px;")
        self._elapsedLabel.setText("")

    def _blink(self):
        self._blink_on = not self._blink_on
        color = "#00C853" if self._blink_on else "#005a20"
        self._dotLabel.setStyleSheet(f"color:{color}; font-size:16px;")

    def _update_elapsed(self):
        import time as _time
        if self._start_time is None:
            return
        secs = int(_time.time() - self._start_time)
        h, rem = divmod(secs, 3600)
        m, s   = divmod(rem, 60)
        self._elapsedLabel.setText(f"{h:02d}:{m:02d}:{s:02d}")

    # ── 자동매매 제어 ─────────────────────────────────────────────

    def _start(self):
        # 혹시 이전 worker가 남아 있으면 신호 연결 해제 후 finishing 셋으로 이관
        if self._worker is not None:
            try:
                self._worker.log.disconnect(self._log)
                self._worker.stopped.disconnect(self._on_stopped)
            except TypeError:
                pass
            self._finishing_workers.add(self._worker)  # ref 유지
            self._worker = None

        broker_idx = self.brokerCombo.currentIndex()
        panel = self._kiwoomPanel if broker_idx == 0 else self._kisPanel

        err = panel.validate()
        if err:
            self._log(err)
            return

        paper = self._kisPanel.is_paper() if broker_idx == 1 else self.kiwoomPaperCheck.isChecked()

        params = {
            "broker_type": "kiwoom" if broker_idx == 0 else "kis",
            "ticker":      self.tickerEdit.text().strip(),
            "rsi_period":  self.rsiSpin.value(),
            "oversold":    self.buyRsiSpin.value(),
            "overbought":  self.sellRsiSpin.value(),
            "macd_fast":   self.macdFastSpin.value(),
            "macd_slow":   self.macdSlowSpin.value(),
            "macd_signal": self.macdSigSpin.value(),
            "buy_ratio":   self.buyRatioSpin.value(),
            "paper":       paper,
            **panel.extra_params(),
        }

        self._save_settings()   # 시작 직전 최신 값 저장

        mode = "모의매매" if paper else "⚠️ 실제매매"
        broker_name = self.brokerCombo.currentText()
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sep = "─" * 52
        self._log(f"\n{sep}")
        self._log(f"▶  자동매매 시작  /  {now_str}")
        self._log(f"   모드: {mode}  |  브로커: {broker_name}  |  종목: {params['ticker']}")
        self._log(sep)

        self._worker = TradeWorker(params)
        self._worker.log.connect(self._log)
        self._worker.stopped.connect(self._on_stopped)
        # run() 완전 반환 후 Qt 이벤트 루프가 안전하게 정리하도록 연결
        self._worker.finished.connect(self._on_worker_finished)
        self._worker.start()

        self.startBtn.setEnabled(False)
        self.stopBtn.setEnabled(True)
        self._stateLabel.setText("실행 중")
        self._stateLabel.setStyleSheet("color:#00C853; font-size:12px; font-weight:bold;")
        self._start_indicator()

    def _stop(self):
        if self._worker:
            self._worker.stop()
        self._log("■  중지 요청됨 — 현재 작업 완료 후 종료합니다…")
        # 버튼은 _on_stopped에서 복구 — 중지 중 상태 표시
        self.stopBtn.setEnabled(False)
        self._stateLabel.setText("중지 중…")
        self._stateLabel.setStyleSheet("color:#FFA000; font-size:12px;")

    def _on_stopped(self):
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._log(f"◼  자동매매 종료  /  {now_str}")
        self._log("─" * 52)
        self.startBtn.setEnabled(True)
        self.stopBtn.setEnabled(False)
        self._stop_indicator()
        # stopped 시점엔 run()이 아직 반환 중 — Python ref를 살려두고
        # finished 신호에서 정리한다 (_on_worker_finished)
        if self._worker is not None:
            self._finishing_workers.add(self._worker)
            self._worker = None

    def _on_worker_finished(self):
        """QThread.finished — run()이 완전히 반환된 뒤 호출됨. 안전하게 삭제."""
        w = self.sender()
        self._finishing_workers.discard(w)
        if w is not None:
            w.deleteLater()
        if self._worker is w:
            self._worker = None

    def _log(self, msg):
        self.logEdit.append(msg)
