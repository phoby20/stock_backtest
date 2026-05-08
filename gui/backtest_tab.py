import traceback
import os

import pandas as pd
import matplotlib
import matplotlib.font_manager as fm
import matplotlib.dates as mdates
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.gridspec import GridSpec

from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QGroupBox, QLabel, QLineEdit, QComboBox, QSpinBox,
    QDoubleSpinBox, QPushButton, QTextEdit, QTableWidget,
    QTableWidgetItem, QSplitter, QHeaderView, QScrollArea,
    QSizePolicy, QFrame, QAbstractSpinBox,
)

from gui.widgets import form_row, hline, make_scroll_sidebar

# ── 폰트 (크로스 플랫폼 한글) ────────────────────────────────────
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_FONT_PATH = os.path.join(_ROOT, "src", "fonts", "NanumGothic.ttf")
if os.path.exists(_FONT_PATH):
    fm.fontManager.addfont(_FONT_PATH)
    matplotlib.rcParams["font.family"] = "NanumGothic"
else:
    _FALLBACKS = ["AppleGothic", "Malgun Gothic", "NanumGothic", "sans-serif"]
    _avail = {f.name for f in fm.fontManager.ttflist}
    matplotlib.rcParams["font.family"] = next(
        (f for f in _FALLBACKS if f in _avail), "sans-serif"
    )

matplotlib.rcParams["axes.unicode_minus"] = False
matplotlib.rcParams.update({
    "figure.facecolor":  "#0d1117",
    "axes.facecolor":    "#161b22",
    "axes.edgecolor":    "#30363d",
    "axes.labelcolor":   "#8b949e",
    "xtick.color":       "#8b949e",
    "ytick.color":       "#8b949e",
    "grid.color":        "#21262d",
    "text.color":        "#c9d1d9",
    "legend.facecolor":  "#161b22",
    "legend.edgecolor":  "#30363d",
    "legend.labelcolor": "#c9d1d9",
})

CANDLE_OPTIONS = [
    ("1m",  "1분봉  (7일)",    10),
    ("5m",  "5분봉  (60일)",   10),
    ("15m", "15분봉 (60일)",   10),
    ("30m", "30분봉 (60일)",   10),
    ("1h",  "1시간봉 (2년)",   12),
    ("1d",  "일봉   (5년)",    20),
]


# ── 통계 카드 ──────────────────────────────────────────────────────
class StatCard(QFrame):
    def __init__(self, title: str):
        super().__init__()
        self.setStyleSheet(
            "QFrame { background:#161b22; border:1px solid #21262d; border-radius:8px; }"
        )
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setMinimumWidth(80)

        vl = QVBoxLayout(self)
        vl.setContentsMargins(14, 10, 14, 10)
        vl.setSpacing(4)

        t = QLabel(title)
        t.setStyleSheet(
            "color:#8b949e; font-size:11px; font-weight:600;"
            "background:transparent; border:none;"
        )
        self._val = QLabel("—")
        self._val.setStyleSheet(
            "color:#e6edf3; font-size:18px; font-weight:700;"
            "background:transparent; border:none;"
        )
        vl.addWidget(t)
        vl.addWidget(self._val)

    def set_value(self, text: str, color: str = "#e6edf3"):
        self._val.setText(text)
        self._val.setStyleSheet(
            f"color:{color}; font-size:18px; font-weight:700;"
            "background:transparent; border:none;"
        )

    def reset(self):
        self._val.setText("—")
        self._val.setStyleSheet(
            "color:#e6edf3; font-size:18px; font-weight:700;"
            "background:transparent; border:none;"
        )


# ── 인라인 차트 캔버스 (hover 툴팁 + 수직 커서 포함) ─────────────
class ChartCanvas(FigureCanvas):
    def __init__(self):
        self._fig = Figure(figsize=(14, 10))
        self._fig.patch.set_facecolor("#0d1117")
        super().__init__(self._fig)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumHeight(500)
        self.setStyleSheet("background:#0d1117;")
        self.setMouseTracking(True)

        self._df     = None          # 현재 차트 데이터프레임
        self._pf     = None          # 포트폴리오 시계열
        self._vlines = []            # 수직 커서 라인 (패널 4개)

        self.mpl_connect("motion_notify_event", self._on_hover)
        self.mpl_connect("figure_leave_event",  self._on_leave)

    # ── 차트 그리기 ────────────────────────────────────────────────
    def draw_result(self, result):
        from src.indicators.macd import calculate_macd
        from PyQt5.QtWidgets import QToolTip
        QToolTip.hideText()

        self._fig.clear()
        self._vlines = []

        df = result.signals_df.copy()
        if "MACD" not in df.columns:
            ml, sl, hl = calculate_macd(df["Close"])
            df["MACD"] = ml
            df["MACD_Signal"] = sl
            df["MACD_Hist"] = hl

        pf = self._build_portfolio(result)
        self._df = df
        self._pf = pf

        # 웹과 동일한 비율: 종가 2 : RSI 1 : MACD 1 : 자산 1.1
        gs = GridSpec(4, 1, figure=self._fig, hspace=0.04,
                      height_ratios=[2, 1, 1, 1.1])
        ax_p = self._fig.add_subplot(gs[0])
        ax_r = self._fig.add_subplot(gs[1], sharex=ax_p)
        ax_m = self._fig.add_subplot(gs[2], sharex=ax_p)
        ax_f = self._fig.add_subplot(gs[3], sharex=ax_p)

        x = df.index
        rate_sign = "+" if result.return_rate >= 0 else ""

        # ── Panel 1: 종가 ─────────────────────────────────────────
        ax_p.fill_between(x, df["Close"], alpha=0.10, color="#4C9BE8")
        ax_p.plot(x, df["Close"], color="#4C9BE8", linewidth=1.5)
        buys  = df[df["Signal"] == "BUY"]
        sells = df[df["Signal"] == "SELL"]
        ax_p.scatter(buys.index,  buys["Close"],  marker="^",
                     color="#00C853", s=80, zorder=5)
        ax_p.scatter(sells.index, sells["Close"], marker="v",
                     color="#FF3D00", s=80, zorder=5)
        ax_p.set_title(
            f"{result.ticker}  [{result._candle_label} / {result._strategy_label}]  "
            f"수익률: {rate_sign}{result.return_rate:.2f}%  |  "
            f"{x[0].strftime('%Y-%m-%d')} ~ {x[-1].strftime('%Y-%m-%d')}",
            fontsize=11, pad=6, color="#c9d1d9",
        )
        ax_p.text(0.005, 0.97, "종가", transform=ax_p.transAxes,
                  fontsize=8, color="#8b949e", va="top")
        ax_p.text(0.99, 0.97, "— 종가   ▲ 매수   ▽ 매도",
                  transform=ax_p.transAxes, fontsize=8,
                  color="#8b949e", va="top", ha="right")
        ax_p.grid(True, alpha=0.3, linestyle="--", linewidth=0.5)
        ax_p.tick_params(labelbottom=False)

        # ── Panel 2: RSI ──────────────────────────────────────────
        ax_r.text(0.005, 0.97, "RSI", transform=ax_r.transAxes,
                  fontsize=8, color="#8b949e", va="top")
        ax_r.plot(x, df["RSI"], color="#AB47BC", linewidth=1.2)
        ax_r.axhline(70, color="#FF3D00", linestyle="--", linewidth=0.9, alpha=0.8)
        ax_r.axhline(30, color="#00C853", linestyle="--", linewidth=0.9, alpha=0.8)
        ax_r.set_ylim(0, 100)
        ax_r.set_yticks([0, 30, 70, 100])
        ax_r.text(0.995, 0.73, "매도(70)", transform=ax_r.transAxes,
                  fontsize=7, color="#FF3D00", ha="right", va="center")
        ax_r.text(0.995, 0.27, "매수(30)", transform=ax_r.transAxes,
                  fontsize=7, color="#00C853", ha="right", va="center")
        ax_r.grid(True, alpha=0.3, linestyle="--", linewidth=0.5)
        ax_r.tick_params(labelbottom=False)

        # ── Panel 3: MACD ─────────────────────────────────────────
        ax_m.text(0.005, 0.97, "MACD", transform=ax_m.transAxes,
                  fontsize=8, color="#8b949e", va="top")
        ax_m.text(0.99, 0.97, "— MACD   — Signal",
                  transform=ax_m.transAxes, fontsize=8,
                  color="#8b949e", va="top", ha="right")
        hist = df["MACD_Hist"]
        bw = (x[1] - x[0]).total_seconds() / 86400 * 0.3 if len(x) > 1 else 0.001
        ax_m.bar(x, hist,
                 color=["#00C853" if v >= 0 else "#FF3D00" for v in hist],
                 alpha=0.5, width=bw)
        ax_m.plot(x, df["MACD"],        color="#4C9BE8", linewidth=1.2)
        ax_m.plot(x, df["MACD_Signal"], color="#F57F17", linewidth=1.2)
        ax_m.axhline(0, color="#8b949e", linewidth=0.5, alpha=0.5)
        ax_m.grid(True, alpha=0.3, linestyle="--", linewidth=0.5)
        ax_m.tick_params(labelbottom=False)

        # ── Panel 4: 자산 ─────────────────────────────────────────
        ax_f.text(0.005, 0.97, "자산", transform=ax_f.transAxes,
                  fontsize=8, color="#8b949e", va="top")
        ax_f.fill_between(pf.index, pf.values, alpha=0.10, color="#00C853")
        ax_f.plot(pf.index, pf.values, color="#00C853", linewidth=1.2)
        ax_f.axhline(result.initial_capital, color="#8b949e",
                     linestyle="--", linewidth=0.8, alpha=0.7)
        cap_fmt = f"{result.initial_capital:,.0f}"
        ax_f.text(0.99, 0.97, f"초기자본 {cap_fmt}",
                  transform=ax_f.transAxes, fontsize=7,
                  color="#8b949e", va="top", ha="right")
        ax_f.set_xlabel("날짜")
        ax_f.grid(True, alpha=0.3, linestyle="--", linewidth=0.5)
        ax_f.xaxis.set_major_formatter(mdates.DateFormatter("%m/%d"))
        self._fig.autofmt_xdate(rotation=30, ha="right")
        self._fig.tight_layout()

        # 수직 커서 라인 (초기 숨김) — 4개 패널 전체
        for ax in (ax_p, ax_r, ax_m, ax_f):
            vl = ax.axvline(x=x[0], color="#8b949e",
                            linewidth=0.8, linestyle="--", alpha=0.7,
                            visible=False, zorder=10)
            self._vlines.append(vl)

        self.draw()

    # ── hover: 수직 커서 + QToolTip ───────────────────────────────
    def _on_hover(self, event):
        from PyQt5.QtWidgets import QToolTip
        from PyQt5.QtCore import QPoint

        if self._df is None or event.xdata is None:
            self._hide_cursor()
            return

        try:
            # 마우스 x 좌표 → 가장 가까운 데이터 인덱스
            dt  = mdates.num2date(event.xdata).replace(tzinfo=None)
            idx = self._df.index.get_indexer([dt], method="nearest")[0]
            if not (0 <= idx < len(self._df)):
                self._hide_cursor()
                return

            # 수직 커서 이동
            x_num = mdates.date2num(self._df.index[idx])
            for vl in self._vlines:
                vl.set_xdata([x_num, x_num])
                vl.set_visible(True)
            self.draw_idle()

            # 툴팁 텍스트 조립 (웹 툴팁과 동일한 항목)
            row      = self._df.iloc[idx]
            date_val = self._df.index[idx]
            pf_val   = float(self._pf.iloc[idx]) if self._pf is not None else None

            date_str = (
                date_val.strftime("%Y-%m-%d %H:%M")
                if (date_val.hour or date_val.minute)
                else date_val.strftime("%Y-%m-%d")
            )

            lines = [f"<b>{date_str}</b>"]
            lines.append(f"종가: {float(row['Close']):,.2f}")

            rsi = row.get("RSI")
            if pd.notna(rsi):
                lines.append(f"RSI: {float(rsi):.2f}")

            macd_v = row.get("MACD")
            if pd.notna(macd_v):
                lines.append(f"MACD: {float(macd_v):.4f}")
                lines.append(f"Signal: {float(row['MACD_Signal']):.4f}")
                lines.append(f"Hist: {float(row['MACD_Hist']):.4f}")

            if pf_val is not None:
                lines.append(f"자산: {pf_val:,.2f}")

            sig = str(row.get("Signal", "HOLD"))
            if sig == "BUY":
                lines.append('<span style="color:#00C853">▲ BUY</span>')
            elif sig == "SELL":
                lines.append('<span style="color:#FF3D00">▽ SELL</span>')

            tip = "<br>".join(lines)

            # QCursor.pos()로 실제 마우스 위치를 가져와 오른쪽에 표시
            from PyQt5.QtGui import QCursor
            cursor_pos = QCursor.pos()
            QToolTip.showText(
                QPoint(cursor_pos.x() + 16, cursor_pos.y()),
                tip, self,
            )

        except Exception:
            self._hide_cursor()

    def _on_leave(self, event):
        from PyQt5.QtWidgets import QToolTip
        self._hide_cursor()
        QToolTip.hideText()

    def _hide_cursor(self):
        if any(vl.get_visible() for vl in self._vlines):
            for vl in self._vlines:
                vl.set_visible(False)
            self.draw_idle()

    # ── 포트폴리오 시계열 (수수료 반영) ────────────────────────────
    @staticmethod
    def _build_portfolio(result) -> pd.Series:
        df = result.signals_df
        trade_by_date = {t.date: t for t in result.trades}
        capital, shares, out = result.initial_capital, 0.0, []

        for date, row in df.iterrows():
            date_str = (
                date.strftime("%Y-%m-%d %H:%M")
                if (date.hour or date.minute)
                else str(date.date())
            )
            trade = trade_by_date.get(date_str)
            if trade:
                if trade.action == "BUY":
                    capital = 0.0
                    shares  = trade.shares
                elif trade.action in ("SELL", "SELL(종료)"):
                    capital = trade.amount
                    shares  = 0.0
            out.append((date, capital + shares * row["Close"]))

        return pd.Series([v for _, v in out], index=[d for d, _ in out])


# ── 백테스트 워커 ─────────────────────────────────────────────────
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
            self.log.emit(
                f"종목: {info['name']}  |  {info['exchange']}  |  {info['currency']}"
            )

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
                {
                    "macd_fast":    p["macd_fast"],
                    "macd_slow":    p["macd_slow"],
                    "macd_signal":  p["macd_signal"],
                    "rsi_lookback": p["rsi_lookback"],
                }
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


# ── 백테스트 탭 ───────────────────────────────────────────────────
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

        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(1)
        splitter.setChildrenCollapsible(False)

        # ── 사이드바 ──────────────────────────────────────────
        inner = QWidget()
        inner.setStyleSheet("background:#161b22;")
        sv = QVBoxLayout(inner)
        sv.setContentsMargins(14, 14, 14, 14)
        sv.setSpacing(14)

        # 종목 · 데이터
        g_data = QGroupBox("종목 · 데이터")
        gv = QVBoxLayout(g_data)
        gv.setSpacing(8)

        self.tickerEdit = QLineEdit("SOXL")
        self.tickerEdit.setPlaceholderText("예: SOXL, 005930.KS")
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
        self.capitalSpin.setRange(1, 10_000_000)
        self.capitalSpin.setValue(1_000)
        self.capitalSpin.setSingleStep(100)
        self.capitalSpin.setGroupSeparatorShown(True)
        self.capitalSpin.setButtonSymbols(QAbstractSpinBox.PlusMinus)
        gv.addWidget(form_row("초기 자본금", self.capitalSpin))

        self.commSpin = QDoubleSpinBox()
        self.commSpin.setRange(0, 1)
        self.commSpin.setDecimals(3)
        self.commSpin.setValue(0.15)
        self.commSpin.setSingleStep(0.001)
        self.commSpin.setSuffix(" %")
        self.commSpin.setButtonSymbols(QAbstractSpinBox.PlusMinus)
        gv.addWidget(form_row("수수료", self.commSpin))
        sv.addWidget(g_data)

        # RSI 전략
        g_rsi = QGroupBox("RSI 전략")
        rv = QVBoxLayout(g_rsi)
        rv.setSpacing(8)

        self.strategyCombo = QComboBox()
        self.strategyCombo.addItems(["RSI 단독", "RSI + MACD"])
        self.strategyCombo.currentIndexChanged.connect(self._on_strategy_changed)
        rv.addWidget(form_row("전략 선택", self.strategyCombo))

        self.rsiPeriodSpin = QSpinBox()
        self.rsiPeriodSpin.setRange(2, 50)
        self.rsiPeriodSpin.setValue(14)
        self.rsiPeriodSpin.setButtonSymbols(QAbstractSpinBox.PlusMinus)
        rv.addWidget(form_row("RSI 기간", self.rsiPeriodSpin))

        self.oversoldSpin = QDoubleSpinBox()
        self.oversoldSpin.setRange(1, 49)
        self.oversoldSpin.setValue(30)
        self.oversoldSpin.setButtonSymbols(QAbstractSpinBox.PlusMinus)
        rv.addWidget(form_row("매수 기준 (RSI ≤)", self.oversoldSpin))

        self.overboughtSpin = QDoubleSpinBox()
        self.overboughtSpin.setRange(51, 99)
        self.overboughtSpin.setValue(70)
        self.overboughtSpin.setButtonSymbols(QAbstractSpinBox.PlusMinus)
        rv.addWidget(form_row("매도 기준 (RSI ≥)", self.overboughtSpin))
        sv.addWidget(g_rsi)

        # MACD 설정
        self.g_macd = QGroupBox("MACD 설정")
        mv_macd = QVBoxLayout(self.g_macd)
        mv_macd.setSpacing(8)

        self.macdFastSpin   = QSpinBox()
        self.macdFastSpin.setRange(2, 100)
        self.macdFastSpin.setValue(12)
        self.macdFastSpin.setButtonSymbols(QAbstractSpinBox.PlusMinus)
        self.macdSlowSpin   = QSpinBox()
        self.macdSlowSpin.setRange(2, 200)
        self.macdSlowSpin.setValue(26)
        self.macdSlowSpin.setButtonSymbols(QAbstractSpinBox.PlusMinus)
        self.macdSignalSpin = QSpinBox()
        self.macdSignalSpin.setRange(2, 50)
        self.macdSignalSpin.setValue(9)
        self.macdSignalSpin.setButtonSymbols(QAbstractSpinBox.PlusMinus)
        mv_macd.addWidget(form_row("단기 EMA", self.macdFastSpin))
        mv_macd.addWidget(form_row("장기 EMA", self.macdSlowSpin))
        mv_macd.addWidget(form_row("시그널",   self.macdSignalSpin))
        mv_macd.addWidget(hline())

        self.lookbackSpin = QSpinBox()
        self.lookbackSpin.setRange(1, 100)
        self.lookbackSpin.setValue(20)
        self.lookbackSpin.setButtonSymbols(QAbstractSpinBox.PlusMinus)
        self.lookbackSpin.setToolTip(
            "RSI 조건을 기억할 봉 수.\n"
            "골든/데드크로스 시점에 최근 N봉 안에\n"
            "RSI 조건 충족 이력이 있으면 매매합니다."
        )
        self.lookbackAutoLbl = QLabel("● 봉 단위 기준 자동 설정됨")
        self.lookbackAutoLbl.setStyleSheet(
            "color:#388bfd; font-size:11px; background:transparent;"
        )
        mv_macd.addWidget(form_row("RSI Lookback (봉)", self.lookbackSpin,
                                   "봉 단위 변경 시 자동 최적값 적용 / 수동 조정 가능"))
        mv_macd.addWidget(self.lookbackAutoLbl)
        sv.addWidget(self.g_macd)
        self.g_macd.setVisible(False)

        sv.addStretch()
        sv.addWidget(hline())

        self.runBtn = QPushButton("▶   백테스트 실행")
        self.runBtn.setObjectName("primaryBtn")
        self.runBtn.setMinimumHeight(38)
        self.runBtn.clicked.connect(self._run)
        sv.addWidget(self.runBtn)

        sidebar_scroll = make_scroll_sidebar(inner)
        splitter.addWidget(sidebar_scroll)

        # ── 메인 영역 ──────────────────────────────────────────
        main_scroll = QScrollArea()
        main_scroll.setWidgetResizable(True)
        main_scroll.setStyleSheet(
            "QScrollArea { border:none; background:#0d1117; }"
            "QScrollArea > QWidget > QWidget { background:#0d1117; }"
        )
        main_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        main_content = QWidget()
        main_content.setStyleSheet("background:#0d1117;")
        ml = QVBoxLayout(main_content)
        ml.setContentsMargins(20, 14, 20, 14)
        ml.setSpacing(12)

        # 플레이스홀더 (결과 없을 때)
        self.placeholderLbl = QLabel("종목을 입력하고 백테스트를 실행하세요.")
        self.placeholderLbl.setAlignment(Qt.AlignCenter)
        self.placeholderLbl.setMinimumHeight(120)
        self.placeholderLbl.setStyleSheet(
            "color:#484f58; font-size:15px; background:#161b22;"
            "border:1px solid #21262d; border-radius:8px;"
        )
        ml.addWidget(self.placeholderLbl)

        # 결과 영역 (초기 숨김)
        self.resultWidget = QWidget()
        self.resultWidget.setStyleSheet("background:transparent;")
        rl = QVBoxLayout(self.resultWidget)
        rl.setContentsMargins(0, 0, 0, 0)
        rl.setSpacing(12)

        # 통계 카드 행
        cards_row = QHBoxLayout()
        cards_row.setSpacing(8)
        self.cardReturn   = StatCard("수익률")
        self.cardProfit   = StatCard("총 수익")
        self.cardTrades   = StatCard("거래횟수")
        self.cardWinRate  = StatCard("승률")
        self.cardMDD      = StatCard("최대낙폭 (MDD)")
        for c in [self.cardReturn, self.cardProfit, self.cardTrades,
                  self.cardWinRate, self.cardMDD]:
            cards_row.addWidget(c)
        rl.addLayout(cards_row)

        # 인라인 차트
        self.chartCanvas = ChartCanvas()
        rl.addWidget(self.chartCanvas)

        # 거래 내역
        trade_lbl = QLabel("거래 내역")
        trade_lbl.setObjectName("sectionLabel")
        rl.addWidget(trade_lbl)

        cols = ["날짜 / 시간", "구분", "가격", "거래금액", "RSI", "수수료"]
        self.tradeTable = QTableWidget(0, len(cols))
        self.tradeTable.setHorizontalHeaderLabels(cols)
        self.tradeTable.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tradeTable.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tradeTable.setAlternatingRowColors(True)
        self.tradeTable.verticalHeader().setVisible(False)
        self.tradeTable.setShowGrid(False)
        self.tradeTable.setMinimumHeight(180)
        rl.addWidget(self.tradeTable)

        ml.addWidget(self.resultWidget)
        self.resultWidget.setVisible(False)

        # 로그 (항상 표시)
        log_lbl = QLabel("실행 로그")
        log_lbl.setObjectName("sectionLabel")
        ml.addWidget(log_lbl)

        self.logEdit = QTextEdit()
        self.logEdit.setReadOnly(True)
        self.logEdit.setFixedHeight(80)
        ml.addWidget(self.logEdit)

        main_scroll.setWidget(main_content)
        splitter.addWidget(main_scroll)

        # 초기 스플리터 비율 (사이드바:메인 ≈ 1:3.5)
        splitter.setSizes([260, 900])
        root.addWidget(splitter)

        self._on_candle_changed(self.candleCombo.currentIndex())

    # ── 이벤트 ────────────────────────────────────────────────────
    def _on_candle_changed(self, idx):
        _, _, lb = CANDLE_OPTIONS[idx]
        self.lookbackSpin.setValue(lb)
        self.lookbackAutoLbl.setText(f"● 자동 설정값: {lb}봉")

    def _on_strategy_changed(self, idx):
        self.g_macd.setVisible(idx == 1)

    # ── 실행 ──────────────────────────────────────────────────────
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
        self._update_cards(result)
        self._update_table(result)
        self.chartCanvas.draw_result(result)
        self.placeholderLbl.setVisible(False)
        self.resultWidget.setVisible(True)
        self._log("완료!")

    def _on_error(self, msg):
        self.runBtn.setEnabled(True)
        self._log(f"[오류] {msg}")

    def _log(self, msg):
        self.logEdit.append(msg)

    def _update_cards(self, r):
        profit_color = "#3fb950" if r.total_profit >= 0 else "#f85149"
        self.cardReturn.set_value(f"{r.return_rate:+.2f}%", profit_color)
        self.cardProfit.set_value(f"{r.total_profit:+,.0f}", profit_color)
        self.cardTrades.set_value(str(r.total_trades))
        win_color = "#3fb950" if r.win_rate >= 50 else "#f85149"
        self.cardWinRate.set_value(f"{r.win_rate:.1f}%", win_color)
        mdd_color = "#f85149" if r.max_drawdown > 10 else "#e6edf3"
        self.cardMDD.set_value(f"{r.max_drawdown:.2f}%", mdd_color)

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
