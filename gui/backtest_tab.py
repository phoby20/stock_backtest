import traceback

from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QGroupBox, QLabel, QLineEdit, QComboBox, QSpinBox,
    QDoubleSpinBox, QPushButton, QTextEdit, QTableWidget,
    QTableWidgetItem, QSplitter, QHeaderView,
)

from gui.widgets import form_row, hline, make_scroll_sidebar

import matplotlib
matplotlib.rcParams["font.family"] = "Malgun Gothic"
matplotlib.rcParams["axes.unicode_minus"] = False

CANDLE_OPTIONS = [
    ("1m",  "1분봉  (7일)",    10),
    ("5m",  "5분봉  (60일)",   10),
    ("15m", "15분봉 (60일)",   10),
    ("30m", "30분봉 (60일)",   10),
    ("1h",  "1시간봉 (2년)",   12),
    ("1d",  "일봉   (5년)",    20),
]


# ── 백테스트 워커 ────────────────────────────────────────────────
class BacktestWorker(QThread):
    finished = pyqtSignal(object)
    error    = pyqtSignal(str)
    log      = pyqtSignal(str)

    def __init__(self, params):
        super().__init__()
        self.params = params

    def run(self):
        try:
            from src.data.fetcher import fetch_historical_data, fetch_ticker_info
            from src.backtest.engine import run_backtest
            from src.strategy.rsi_strategy import generate_signals as rsi_fn
            from src.strategy.rsi_macd_strategy import generate_signals as rsi_macd_fn

            p = self.params
            self.log.emit(f"데이터 수집 중… ({p['ticker']} / {p['candle_label']})")

            info = fetch_ticker_info(p["ticker"])
            self.log.emit(f"종목: {info['name']}  |  {info['exchange']}  |  {info['currency']}")

            df = fetch_historical_data(
                p["ticker"], interval=p["candle"],
                custom_period=p.get("period") or None,
            )
            self.log.emit(
                f"수집: {df.index[0].strftime('%Y-%m-%d %H:%M')} ~ "
                f"{df.index[-1].strftime('%Y-%m-%d %H:%M')}  ({len(df):,}봉)"
            )

            is_macd     = p["strategy"] == "rsi-macd"
            strategy_fn = rsi_macd_fn if is_macd else rsi_fn
            s_kwargs    = (
                {"macd_fast": p["macd_fast"], "macd_slow": p["macd_slow"],
                 "macd_signal": p["macd_signal"], "rsi_lookback": p["rsi_lookback"]}
                if is_macd else {}
            )

            result = run_backtest(
                ticker=p["ticker"], df=df,
                initial_capital=p["capital"],
                rsi_period=p["rsi_period"],
                oversold=p["oversold"], overbought=p["overbought"],
                commission_rate=p["commission"],
                strategy_fn=strategy_fn, strategy_kwargs=s_kwargs,
            )
            result._candle_label   = p["candle_label"]
            result._strategy_label = p["strategy_label"]
            self.finished.emit(result)

        except Exception as e:
            self.error.emit(f"{e}\n{traceback.format_exc()}")


# ── 백테스트 탭 ──────────────────────────────────────────────────
class BacktestTab(QWidget):
    def __init__(self):
        super().__init__()
        self._worker = None
        self._result = None
        self._setup_ui()

    def _setup_ui(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── 사이드바 내용 (스크롤 가능) ──────────────────────
        inner = QWidget()
        inner.setStyleSheet("background:#161b22;")
        sv = QVBoxLayout(inner)
        sv.setContentsMargins(14, 14, 14, 14)
        sv.setSpacing(10)

        # ▶ 종목 / 데이터
        g_data = QGroupBox("종목 · 데이터")
        gv = QVBoxLayout(g_data)
        gv.setSpacing(8)

        self.tickerEdit = QLineEdit("SOXL")
        self.tickerEdit.setPlaceholderText("예: AAPL, 005930.KS")
        gv.addWidget(form_row("종목코드", self.tickerEdit))

        self.candleCombo = QComboBox()
        for _, label, _ in CANDLE_OPTIONS:
            self.candleCombo.addItem(label)
        self.candleCombo.setCurrentIndex(5)
        self.candleCombo.currentIndexChanged.connect(self._on_candle_changed)
        gv.addWidget(form_row("봉 단위", self.candleCombo))

        self.periodEdit = QLineEdit()
        self.periodEdit.setPlaceholderText("빈칸=최대  |  예: 14d · 60d · 1y")
        gv.addWidget(form_row("기간 지정", self.periodEdit,
                              "비워두면 봉 단위 최대 기간 자동 적용"))

        self.capitalSpin = QDoubleSpinBox()
        self.capitalSpin.setRange(1, 1_000_000_000)
        self.capitalSpin.setValue(10_000_000)
        self.capitalSpin.setSingleStep(1_000_000)
        self.capitalSpin.setGroupSeparatorShown(True)
        gv.addWidget(form_row("초기 자본금", self.capitalSpin))

        self.commSpin = QDoubleSpinBox()
        self.commSpin.setRange(0, 1); self.commSpin.setDecimals(3)
        self.commSpin.setValue(0.015); self.commSpin.setSingleStep(0.001)
        self.commSpin.setSuffix(" %")
        gv.addWidget(form_row("수수료", self.commSpin))
        sv.addWidget(g_data)

        # ▶ RSI 전략
        g_rsi = QGroupBox("RSI 전략")
        rv = QVBoxLayout(g_rsi)
        rv.setSpacing(8)

        self.strategyCombo = QComboBox()
        self.strategyCombo.addItems(["RSI 단독", "RSI + MACD"])
        self.strategyCombo.currentIndexChanged.connect(self._on_strategy_changed)
        rv.addWidget(form_row("전략 선택", self.strategyCombo))

        self.rsiPeriodSpin = QSpinBox()
        self.rsiPeriodSpin.setRange(2, 50); self.rsiPeriodSpin.setValue(14)
        rv.addWidget(form_row("RSI 기간", self.rsiPeriodSpin))

        self.oversoldSpin = QDoubleSpinBox()
        self.oversoldSpin.setRange(1, 49); self.oversoldSpin.setValue(30)
        rv.addWidget(form_row("매수 기준 (RSI ≤)", self.oversoldSpin))

        self.overboughtSpin = QDoubleSpinBox()
        self.overboughtSpin.setRange(51, 99); self.overboughtSpin.setValue(70)
        rv.addWidget(form_row("매도 기준 (RSI ≥)", self.overboughtSpin))
        sv.addWidget(g_rsi)

        # ▶ MACD (RSI+MACD 전략 시만 표시)
        self.g_macd = QGroupBox("MACD 설정")
        mv = QVBoxLayout(self.g_macd)
        mv.setSpacing(8)

        self.macdFastSpin   = QSpinBox(); self.macdFastSpin.setRange(2, 100);  self.macdFastSpin.setValue(12)
        self.macdSlowSpin   = QSpinBox(); self.macdSlowSpin.setRange(2, 200);  self.macdSlowSpin.setValue(26)
        self.macdSignalSpin = QSpinBox(); self.macdSignalSpin.setRange(2, 50); self.macdSignalSpin.setValue(9)
        mv.addWidget(form_row("단기 EMA", self.macdFastSpin))
        mv.addWidget(form_row("장기 EMA", self.macdSlowSpin))
        mv.addWidget(form_row("시그널",   self.macdSignalSpin))

        mv.addWidget(hline())

        self.lookbackSpin = QSpinBox()
        self.lookbackSpin.setRange(1, 100); self.lookbackSpin.setValue(20)
        self.lookbackSpin.setToolTip(
            "RSI 조건을 기억할 봉 수.\n"
            "골든/데드크로스 시점에 최근 N봉 안에\n"
            "RSI 조건 충족 이력이 있으면 매매합니다."
        )
        self.lookbackAutoLbl = QLabel("● 봉 단위 기준 자동 설정됨")
        self.lookbackAutoLbl.setStyleSheet(
            "color:#388bfd; font-size:11px; background:transparent;"
        )
        mv.addWidget(form_row("RSI Lookback (봉)", self.lookbackSpin,
                              "봉 단위 변경 시 자동 최적값 적용 / 수동 조정 가능"))
        mv.addWidget(self.lookbackAutoLbl)
        sv.addWidget(self.g_macd)
        self.g_macd.setVisible(False)

        sv.addStretch()
        sv.addWidget(hline())

        self.runBtn = QPushButton("▶   백테스트 실행")
        self.runBtn.setObjectName("primaryBtn")
        self.runBtn.setMinimumHeight(38)
        self.runBtn.clicked.connect(self._run)
        sv.addWidget(self.runBtn)

        self.chartBtn = QPushButton("📈   차트 보기")
        self.chartBtn.setObjectName("chartBtn")
        self.chartBtn.setMinimumHeight(36)
        self.chartBtn.setEnabled(False)
        self.chartBtn.clicked.connect(self._show_chart)
        sv.addWidget(self.chartBtn)

        # 사이드바를 ScrollArea로 감싸기
        sidebar_scroll = make_scroll_sidebar(inner, min_width=200, max_width=320)
        root.addWidget(sidebar_scroll)

        # ── 메인 영역 ─────────────────────────────────────────
        main = QWidget()
        main.setStyleSheet("background:#0d1117;")
        mav = QVBoxLayout(main)
        mav.setContentsMargins(20, 14, 20, 14)
        mav.setSpacing(10)

        self.summaryLabel = QLabel("종목을 입력하고 백테스트를 실행하세요.")
        self.summaryLabel.setObjectName("resultSummary")
        self.summaryLabel.setWordWrap(True)
        self.summaryLabel.setMinimumHeight(46)
        mav.addWidget(self.summaryLabel)

        col_headers = ["날짜 / 시간", "구분", "가격", "거래금액", "RSI", "수수료"]
        self.tradeTable = QTableWidget(0, len(col_headers))
        self.tradeTable.setHorizontalHeaderLabels(col_headers)
        self.tradeTable.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tradeTable.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tradeTable.setAlternatingRowColors(True)
        self.tradeTable.verticalHeader().setVisible(False)
        self.tradeTable.setShowGrid(False)
        mav.addWidget(self.tradeTable)

        log_lbl = QLabel("실행 로그")
        log_lbl.setObjectName("sectionLabel")
        mav.addWidget(log_lbl)

        self.logEdit = QTextEdit()
        self.logEdit.setReadOnly(True)
        self.logEdit.setMaximumHeight(80)
        mav.addWidget(self.logEdit)

        root.addWidget(main)

        # 초기 lookback 반영
        self._on_candle_changed(self.candleCombo.currentIndex())

    # ── 이벤트 ──────────────────────────────────────────────────
    def _on_candle_changed(self, idx):
        _, _, lb = CANDLE_OPTIONS[idx]
        self.lookbackSpin.setValue(lb)
        self.lookbackAutoLbl.setText(f"● 자동 설정값: {lb}봉")

    def _on_strategy_changed(self, idx):
        self.g_macd.setVisible(idx == 1)

    # ── 실행 ────────────────────────────────────────────────────
    def _run(self):
        idx = self.candleCombo.currentIndex()
        candle_key, candle_label, _ = CANDLE_OPTIONS[idx]
        is_macd  = self.strategyCombo.currentIndex() == 1
        lookback = self.lookbackSpin.value()

        s_label = f"RSI({self.rsiPeriodSpin.value()})"
        if is_macd:
            s_label += (
                f" + MACD({self.macdFastSpin.value()}/"
                f"{self.macdSlowSpin.value()}/"
                f"{self.macdSignalSpin.value()})"
                f"  LB:{lookback}"
            )

        params = {
            "ticker":         self.tickerEdit.text().strip().upper(),
            "candle":         candle_key,
            "candle_label":   candle_label.strip(),
            "period":         self.periodEdit.text().strip() or None,
            "capital":        self.capitalSpin.value(),
            "commission":     self.commSpin.value() / 100,
            "strategy":       "rsi-macd" if is_macd else "rsi",
            "strategy_label": s_label,
            "rsi_period":     self.rsiPeriodSpin.value(),
            "oversold":       self.oversoldSpin.value(),
            "overbought":     self.overboughtSpin.value(),
            "macd_fast":      self.macdFastSpin.value(),
            "macd_slow":      self.macdSlowSpin.value(),
            "macd_signal":    self.macdSignalSpin.value(),
            "rsi_lookback":   lookback,
        }

        self.runBtn.setEnabled(False)
        self.chartBtn.setEnabled(False)
        self.logEdit.clear()
        self._log("실행 중…")

        self._worker = BacktestWorker(params)
        self._worker.log.connect(self._log)
        self._worker.finished.connect(self._on_finished)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    def _on_finished(self, result):
        self._result = result
        self.runBtn.setEnabled(True)
        self.chartBtn.setEnabled(True)
        self._update_summary(result)
        self._update_table(result)
        self._log("완료!")

    def _on_error(self, msg):
        self.runBtn.setEnabled(True)
        self._log(f"[오류] {msg}")

    def _log(self, msg):
        self.logEdit.append(msg)

    def _update_summary(self, r):
        color = "#3fb950" if r.total_profit >= 0 else "#f85149"
        self.summaryLabel.setText(
            f"<b style='color:#58a6ff'>{r.ticker}</b>"
            f"<span style='color:#484f58'>  ·  </span>"
            f"<span style='color:#8b949e'>{r._candle_label}  /  {r._strategy_label}</span><br>"
            f"초기 <b>{r.initial_capital:,.0f}</b>"
            f"<span style='color:#484f58'> → </span>"
            f"최종 <b>{r.final_capital:,.0f}</b>&nbsp;&nbsp;"
            f"<b style='color:{color}'>{r.total_profit:+,.0f}</b>&nbsp;"
            f"<b style='color:{color}'>({r.return_rate:+.2f}%)</b>"
            f"<span style='color:#484f58'>  ·  </span>"
            f"거래 {r.total_trades}회"
            f"<span style='color:#484f58'>  ·  </span>"
            f"승률 {r.win_rate:.1f}%"
            f"<span style='color:#484f58'>  ·  </span>"
            f"MDD {r.max_drawdown:.2f}%"
        )

    def _update_table(self, r):
        self.tradeTable.setRowCount(0)
        for t in r.trades:
            row = self.tradeTable.rowCount()
            self.tradeTable.insertRow(row)
            fg = QColor("#3fb950" if "BUY" in t.action else "#f85149")
            for col, val in enumerate([
                t.date, t.action,
                f"{t.price:,.4f}", f"{t.amount:,.0f}",
                f"{t.rsi:.2f}", f"{t.commission:,.0f}",
            ]):
                item = QTableWidgetItem(val)
                item.setTextAlignment(Qt.AlignCenter)
                if col == 1:
                    item.setForeground(fg)
                self.tradeTable.setItem(row, col, item)

    def _show_chart(self):
        if not self._result:
            return
        from gui.chart_window import ChartWindow
        self._chart_win = ChartWindow(
            self._result,
            candle_label=self._result._candle_label,
            strategy_label=self._result._strategy_label,
        )
        self._chart_win.show()
