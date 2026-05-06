"""
Vercel Python Serverless Function — /api/py_backtest
matplotlib PNG 차트를 base64로 반환
"""
import matplotlib
matplotlib.use("Agg")

import sys
import os
import json
import base64
import traceback
from http.server import BaseHTTPRequestHandler

# 프로젝트 루트를 sys.path에 추가
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

CANDLE_META = {
    "1m":  {"label": "1분봉",   "max_period": "7d",   "auto_lookback": 10},
    "5m":  {"label": "5분봉",   "max_period": "60d",  "auto_lookback": 10},
    "15m": {"label": "15분봉",  "max_period": "60d",  "auto_lookback": 10},
    "30m": {"label": "30분봉",  "max_period": "60d",  "auto_lookback": 10},
    "1h":  {"label": "1시간봉", "max_period": "730d", "auto_lookback": 12},
    "1d":  {"label": "일봉",    "max_period": "5y",   "auto_lookback": 20},
}


def _run(body: dict) -> dict:
    from src.data.fetcher import fetch_historical_data
    from src.backtest.engine import run_backtest
    from src.utils.chart import render_chart_bytes
    from src.strategy.rsi_macd_strategy import generate_signals as rsi_macd_signals
    from src.strategy.rsi_strategy import generate_signals as rsi_signals

    ticker       = body.get("ticker",       "AAPL")
    candle       = body.get("candle",       "1d")
    capital      = float(body.get("capital",      1_000))
    strategy     = body.get("strategy",     "rsi-macd")
    rsi_period   = int(body.get("rsi_period",   14))
    oversold     = float(body.get("oversold",     30))
    overbought   = float(body.get("overbought",   70))
    macd_fast    = int(body.get("macd_fast",    12))
    macd_slow    = int(body.get("macd_slow",    26))
    macd_signal  = int(body.get("macd_signal",   9))
    rsi_lookback = int(body.get("rsi_lookback", 20))
    custom_period = body.get("custom_period")

    meta         = CANDLE_META.get(candle, {"label": candle, "max_period": "5y", "auto_lookback": 20})
    period       = custom_period or meta["max_period"]
    candle_label = meta["label"]

    df = fetch_historical_data(ticker, period=period, interval=candle)

    if strategy == "rsi-macd":
        strategy_fn     = rsi_macd_signals
        strategy_kwargs = {
            "macd_fast":    macd_fast,
            "macd_slow":    macd_slow,
            "macd_signal":  macd_signal,
            "rsi_lookback": rsi_lookback,
        }
        strategy_label = f"RSI+MACD (lookback={rsi_lookback})"
    else:
        strategy_fn     = rsi_signals
        strategy_kwargs = {}
        strategy_label  = "RSI"

    result = run_backtest(
        ticker=ticker,
        df=df,
        initial_capital=capital,
        rsi_period=rsi_period,
        oversold=oversold,
        overbought=overbought,
        strategy_fn=strategy_fn,
        strategy_kwargs=strategy_kwargs,
    )

    chart_bytes = render_chart_bytes(result, candle_label=candle_label, strategy_label=strategy_label)
    chart_b64   = base64.b64encode(chart_bytes).decode()

    trades = [
        {
            "date":       t.date,
            "action":     t.action,
            "price":      round(t.price, 4),
            "shares":     round(t.shares, 6),
            "amount":     round(t.amount, 2),
            "commission": round(t.commission, 2),
            "rsi":        round(t.rsi, 2),
        }
        for t in result.trades
    ]

    return {
        "ticker":          result.ticker.upper(),
        "candle_label":    candle_label,
        "strategy_label":  strategy_label,
        "period_start":    df.index[0].strftime("%Y-%m-%d"),
        "period_end":      df.index[-1].strftime("%Y-%m-%d"),
        "initial_capital": capital,
        "final_capital":   round(result.final_capital, 2),
        "total_profit":    round(result.total_profit, 2),
        "return_rate":     round(result.return_rate, 4),
        "total_trades":    result.total_trades,
        "win_trades":      result.win_trades,
        "lose_trades":     result.lose_trades,
        "win_rate":        round(result.win_rate, 2),
        "max_drawdown":    round(result.max_drawdown, 2),
        "trades":          trades,
        "chart_png":       chart_b64,
    }


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            body   = json.loads(self.rfile.read(length)) if length else {}
            data   = _run(body)
            self._respond(200, data)
        except Exception as e:
            traceback.print_exc()
            self._respond(400, {"detail": str(e)})

    def _respond(self, status: int, data: dict):
        payload = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type",   "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(payload)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin",  "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def log_message(self, *args):
        pass  # 서버리스 로그 억제
