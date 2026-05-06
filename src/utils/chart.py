import io
import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.font_manager as fm
from matplotlib.gridspec import GridSpec
from src.backtest.engine import BacktestResult
from src.indicators.macd import calculate_macd

# 번들된 NanumGothic 폰트를 우선 사용, 없으면 시스템 폰트 탐색
_FONT_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "fonts", "NanumGothic.ttf")
if os.path.exists(_FONT_PATH):
    fm.fontManager.addfont(_FONT_PATH)
    plt.rcParams["font.family"] = "NanumGothic"
else:
    _FALLBACKS = ["AppleGothic", "Malgun Gothic", "NanumGothic", "sans-serif"]
    _available = {f.name for f in fm.fontManager.ttflist}
    plt.rcParams["font.family"] = next((f for f in _FALLBACKS if f in _available), "sans-serif")

plt.rcParams["axes.unicode_minus"] = False

# 어두운 테마
plt.rcParams.update({
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


def _build_portfolio_series(result: BacktestResult) -> pd.Series:
    df = result.signals_df
    capital = result.initial_capital
    shares = 0.0
    portfolio = []

    for date, row in df.iterrows():
        signal = row["Signal"]
        price = row["Close"]

        if signal == "BUY" and shares == 0 and capital > 0:
            shares = capital / price
            capital = 0.0
        elif signal == "SELL" and shares > 0:
            capital = shares * price
            shares = 0.0

        portfolio.append((date, capital + shares * price))

    return pd.Series(
        [v for _, v in portfolio],
        index=[d for d, _ in portfolio],
        name="Portfolio",
    )


def _build_figure(
    result: BacktestResult,
    candle_label: str = "일봉",
    strategy_label: str = "RSI",
) -> plt.Figure:
    """차트 Figure를 생성해 반환 (plt.show / savefig 미포함)"""
    df = result.signals_df.copy()

    if "MACD" not in df.columns:
        macd_line, signal_line, histogram = calculate_macd(df["Close"])
        df["MACD"] = macd_line
        df["MACD_Signal"] = signal_line
        df["MACD_Hist"] = histogram

    fig = plt.figure(figsize=(16, 12))
    gs  = GridSpec(4, 1, figure=fig, hspace=0.08, height_ratios=[3, 1.5, 1.5, 1.5])

    ax_price = fig.add_subplot(gs[0])
    ax_rsi   = fig.add_subplot(gs[1], sharex=ax_price)
    ax_macd  = fig.add_subplot(gs[2], sharex=ax_price)
    ax_pf    = fig.add_subplot(gs[3], sharex=ax_price)

    x = df.index

    # ── 패널 1: 가격 + 매수/매도 마커 ──────────────────────────
    ax_price.plot(x, df["Close"], color="#4C9BE8", linewidth=1, label="종가")
    ax_price.fill_between(x, df["Close"], alpha=0.08, color="#4C9BE8")

    buy_signals  = df[df["Signal"] == "BUY"]
    sell_signals = df[df["Signal"] == "SELL"]
    ax_price.scatter(buy_signals.index,  buy_signals["Close"],
                     marker="^", color="#00C853", s=130, zorder=5, label="매수")
    ax_price.scatter(sell_signals.index, sell_signals["Close"],
                     marker="v", color="#FF3D00", s=130, zorder=5, label="매도")

    ax_price.set_title(
        f"{result.ticker}  [{candle_label} / {strategy_label}]  "
        f"수익률: {result.return_rate:+.2f}%  |  "
        f"{df.index[0].strftime('%Y-%m-%d')} ~ {df.index[-1].strftime('%Y-%m-%d')}",
        fontsize=13, pad=10,
    )
    ax_price.set_ylabel("가격")
    ax_price.legend(loc="upper left", fontsize=9)
    ax_price.grid(True, alpha=0.3)
    plt.setp(ax_price.get_xticklabels(), visible=False)

    # ── 패널 2: RSI ──────────────────────────────────────────
    ax_rsi.plot(x, df["RSI"], color="#AB47BC", linewidth=1)
    ax_rsi.axhline(70, color="#FF3D00", linestyle="--", linewidth=0.9, alpha=0.8)
    ax_rsi.axhline(30, color="#00C853", linestyle="--", linewidth=0.9, alpha=0.8)
    ax_rsi.fill_between(x, df["RSI"], 70, where=(df["RSI"] >= 70), alpha=0.2, color="#FF3D00")
    ax_rsi.fill_between(x, df["RSI"], 30, where=(df["RSI"] <= 30), alpha=0.2, color="#00C853")
    ax_rsi.set_ylabel("RSI")
    ax_rsi.set_ylim(0, 100)
    ax_rsi.text(x[-1], 73, "과매수(70)", fontsize=7, color="#FF3D00", ha="right")
    ax_rsi.text(x[-1], 23, "과매도(30)", fontsize=7, color="#00C853", ha="right")
    ax_rsi.grid(True, alpha=0.3)
    plt.setp(ax_rsi.get_xticklabels(), visible=False)

    # ── 패널 3: MACD ─────────────────────────────────────────
    ax_macd.plot(x, df["MACD"],        color="#1565C0", linewidth=1, label="MACD")
    ax_macd.plot(x, df["MACD_Signal"], color="#F57F17", linewidth=1, label="Signal")

    hist = df["MACD_Hist"]
    if len(x) > 1:
        delta     = (x[1] - x[0]).total_seconds() / 86400
        bar_width = delta * 0.6
    else:
        bar_width = 0.003
    colors = ["#00C853" if v >= 0 else "#FF3D00" for v in hist]
    ax_macd.bar(x, hist, color=colors, alpha=0.5, width=bar_width)
    ax_macd.axhline(0, color="gray", linewidth=0.6)
    ax_macd.set_ylabel("MACD")
    ax_macd.legend(loc="upper left", fontsize=9)
    ax_macd.grid(True, alpha=0.3)
    plt.setp(ax_macd.get_xticklabels(), visible=False)

    if "MACD_Hist" in df.columns:
        golden = (df["MACD_Hist"].shift(1) < 0) & (df["MACD_Hist"] >= 0)
        dead   = (df["MACD_Hist"].shift(1) > 0) & (df["MACD_Hist"] <= 0)
        ax_macd.scatter(df.index[golden], df["MACD"][golden],
                        marker="^", color="#00C853", s=60, zorder=5)
        ax_macd.scatter(df.index[dead],   df["MACD"][dead],
                        marker="v", color="#FF3D00", s=60, zorder=5)

    # ── 패널 4: 포트폴리오 가치 ──────────────────────────────
    pf           = _build_portfolio_series(result)
    profit_color = "#00C853" if result.total_profit >= 0 else "#FF3D00"
    ax_pf.plot(pf.index, pf.values, color=profit_color, linewidth=1.2)
    ax_pf.fill_between(pf.index, pf.values, result.initial_capital,
                        alpha=0.15, color=profit_color)
    ax_pf.axhline(result.initial_capital, color="gray", linestyle="--",
                  linewidth=0.8, alpha=0.7,
                  label=f"초기자본 {result.initial_capital:,.0f}")
    ax_pf.set_ylabel("자산")
    ax_pf.set_xlabel("날짜")
    ax_pf.legend(loc="upper left", fontsize=9)
    ax_pf.grid(True, alpha=0.3)

    ax_pf.xaxis.set_major_formatter(mdates.DateFormatter("%m/%d"))
    fig.autofmt_xdate(rotation=30, ha="right")
    plt.tight_layout()

    return fig


def plot_backtest(
    result: BacktestResult,
    candle_label: str = "일봉",
    strategy_label: str = "RSI",
    save_path: str = None,
):
    fig = _build_figure(result, candle_label, strategy_label)
    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
        print(f"  차트 저장: {save_path}")
    plt.show()
    plt.close(fig)


def render_chart_bytes(
    result: BacktestResult,
    candle_label: str = "일봉",
    strategy_label: str = "RSI+MACD",
) -> bytes:
    """PNG bytes 반환 (헤드리스 환경 / API 전용 — plt.show 미호출)"""
    fig = _build_figure(result, candle_label, strategy_label)
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf.read()
