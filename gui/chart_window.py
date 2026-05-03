import pandas as pd
import matplotlib
import matplotlib.dates as mdates
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.gridspec import GridSpec
from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout

matplotlib.rcParams["font.family"] = "Malgun Gothic"
matplotlib.rcParams["axes.unicode_minus"] = False
matplotlib.rcParams["figure.facecolor"] = "#1e1e2e"
matplotlib.rcParams["axes.facecolor"]   = "#181825"
matplotlib.rcParams["axes.edgecolor"]   = "#45475a"
matplotlib.rcParams["text.color"]       = "#cdd6f4"
matplotlib.rcParams["axes.labelcolor"]  = "#cdd6f4"
matplotlib.rcParams["xtick.color"]      = "#a6adc8"
matplotlib.rcParams["ytick.color"]      = "#a6adc8"
matplotlib.rcParams["grid.color"]       = "#313244"


def _build_portfolio(result) -> pd.Series:
    df = result.signals_df
    capital, shares, out = result.initial_capital, 0.0, []
    for date, row in df.iterrows():
        if row["Signal"] == "BUY" and shares == 0 and capital > 0:
            shares = capital / row["Close"]; capital = 0.0
        elif row["Signal"] == "SELL" and shares > 0:
            capital = shares * row["Close"]; shares = 0.0
        out.append((date, capital + shares * row["Close"]))
    return pd.Series([v for _, v in out], index=[d for d, _ in out])


class ChartWindow(QMainWindow):
    def __init__(self, result, candle_label="일봉", strategy_label="RSI"):
        super().__init__()
        self.setWindowTitle(f"{result.ticker} — {candle_label} / {strategy_label}")
        self.resize(1200, 750)
        self._draw(result, candle_label, strategy_label)

    def _draw(self, result, candle_label, strategy_label):
        from src.indicators.macd import calculate_macd
        df = result.signals_df.copy()
        if "MACD" not in df.columns:
            ml, sl, hl = calculate_macd(df["Close"])
            df["MACD"] = ml; df["MACD_Signal"] = sl; df["MACD_Hist"] = hl

        fig = Figure(figsize=(14, 10), tight_layout=False)
        gs  = GridSpec(4, 1, figure=fig, hspace=0.08, height_ratios=[3,1.5,1.5,1.5])
        ax_p = fig.add_subplot(gs[0])
        ax_r = fig.add_subplot(gs[1], sharex=ax_p)
        ax_m = fig.add_subplot(gs[2], sharex=ax_p)
        ax_f = fig.add_subplot(gs[3], sharex=ax_p)

        x = df.index

        # 가격
        ax_p.plot(x, df["Close"], color="#89b4fa", lw=1)
        ax_p.fill_between(x, df["Close"], alpha=0.07, color="#89b4fa")
        buys  = df[df["Signal"] == "BUY"]
        sells = df[df["Signal"] == "SELL"]
        ax_p.scatter(buys.index,  buys["Close"],  marker="^", color="#a6e3a1", s=120, zorder=5, label="매수")
        ax_p.scatter(sells.index, sells["Close"], marker="v", color="#f38ba8", s=120, zorder=5, label="매도")
        ax_p.set_title(
            f"{result.ticker}  [{candle_label} / {strategy_label}]  "
            f"수익률: {result.return_rate:+.2f}%  |  "
            f"{x[0].strftime('%Y-%m-%d')} ~ {x[-1].strftime('%Y-%m-%d')}",
            fontsize=12, pad=8, color="#cdd6f4",
        )
        ax_p.set_ylabel("가격", fontsize=10)
        ax_p.legend(fontsize=9, loc="upper left",
                    facecolor="#313244", edgecolor="#45475a", labelcolor="#cdd6f4")
        ax_p.grid(True, alpha=0.25)
        ax_p.tick_params(labelbottom=False)

        # RSI
        ax_r.plot(x, df["RSI"], color="#cba6f7", lw=1)
        ax_r.axhline(70, color="#f38ba8", ls="--", lw=0.9, alpha=0.8)
        ax_r.axhline(30, color="#a6e3a1", ls="--", lw=0.9, alpha=0.8)
        ax_r.fill_between(x, df["RSI"], 70, where=df["RSI"]>=70, alpha=0.18, color="#f38ba8")
        ax_r.fill_between(x, df["RSI"], 30, where=df["RSI"]<=30, alpha=0.18, color="#a6e3a1")
        ax_r.set_ylabel("RSI", fontsize=10)
        ax_r.set_ylim(0, 100)
        ax_r.text(x[-1], 73, "과매수(70)", fontsize=7, color="#f38ba8", ha="right")
        ax_r.text(x[-1], 23, "과매도(30)", fontsize=7, color="#a6e3a1", ha="right")
        ax_r.grid(True, alpha=0.25)
        ax_r.tick_params(labelbottom=False)

        # MACD
        ax_m.plot(x, df["MACD"],        color="#89b4fa", lw=1, label="MACD")
        ax_m.plot(x, df["MACD_Signal"], color="#fab387", lw=1, label="Signal")
        hist = df["MACD_Hist"]
        bw   = (x[1]-x[0]).total_seconds()/86400*0.6 if len(x)>1 else 0.003
        ax_m.bar(x, hist, color=["#a6e3a1" if v>=0 else "#f38ba8" for v in hist], alpha=0.5, width=bw)
        ax_m.axhline(0, color="#6c7086", lw=0.6)
        ax_m.set_ylabel("MACD", fontsize=10)
        ax_m.legend(fontsize=9, loc="upper left",
                    facecolor="#313244", edgecolor="#45475a", labelcolor="#cdd6f4")
        ax_m.grid(True, alpha=0.25)
        ax_m.tick_params(labelbottom=False)

        # 포트폴리오
        pf = _build_portfolio(result)
        pc = "#a6e3a1" if result.total_profit >= 0 else "#f38ba8"
        ax_f.plot(pf.index, pf.values, color=pc, lw=1.2)
        ax_f.fill_between(pf.index, pf.values, result.initial_capital, alpha=0.13, color=pc)
        ax_f.axhline(result.initial_capital, color="#6c7086", ls="--", lw=0.8)
        ax_f.set_ylabel("자산", fontsize=10)
        ax_f.set_xlabel("날짜", fontsize=10)
        ax_f.grid(True, alpha=0.25)
        ax_f.xaxis.set_major_formatter(mdates.DateFormatter("%m/%d"))
        fig.autofmt_xdate(rotation=25, ha="right")

        canvas = FigureCanvas(fig)
        container = QWidget()
        vl = QVBoxLayout(container)
        vl.setContentsMargins(0,0,0,0)
        vl.addWidget(canvas)
        self.setCentralWidget(container)
