# matplotlib은 pyplot import 전에 백엔드 지정해야 함
import matplotlib
matplotlib.use("Agg")

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import base64

app = FastAPI(title="Stock Backtest API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 봉 단위별 메타데이터
CANDLE_META = {
    "1m":  {"label": "1분봉",    "max_period": "7d",   "auto_lookback": 10},
    "5m":  {"label": "5분봉",    "max_period": "60d",  "auto_lookback": 10},
    "15m": {"label": "15분봉",   "max_period": "60d",  "auto_lookback": 10},
    "30m": {"label": "30분봉",   "max_period": "60d",  "auto_lookback": 10},
    "1h":  {"label": "1시간봉",  "max_period": "730d", "auto_lookback": 12},
    "1d":  {"label": "일봉",     "max_period": "5y",   "auto_lookback": 20},
}


class BacktestRequest(BaseModel):
    ticker:       str   = "SOXL"
    candle:       str   = "1d"
    capital:      float = 10_000_000
    strategy:     str   = "rsi-macd"
    rsi_period:   int   = 14
    oversold:     float = 30.0
    overbought:   float = 70.0
    macd_fast:    int   = 12
    macd_slow:    int   = 26
    macd_signal:  int   = 9
    rsi_lookback: int   = 20
    custom_period: Optional[str] = None


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/candle-options")
def candle_options():
    return CANDLE_META


@app.post("/api/backtest")
def run_backtest_endpoint(req: BacktestRequest):
    try:
        from src.data.fetcher import fetch_historical_data
        from src.backtest.engine import run_backtest
        from src.utils.chart import render_chart_bytes

        meta         = CANDLE_META.get(req.candle, {"label": req.candle, "max_period": "5y", "auto_lookback": 20})
        period       = req.custom_period or meta["max_period"]
        candle_label = meta["label"]

        df = fetch_historical_data(req.ticker, period=period, interval=req.candle)

        if req.strategy == "rsi-macd":
            from src.strategy.rsi_macd_strategy import generate_signals
            strategy_fn     = generate_signals
            strategy_kwargs = {
                "macd_fast":    req.macd_fast,
                "macd_slow":    req.macd_slow,
                "macd_signal":  req.macd_signal,
                "rsi_lookback": req.rsi_lookback,
            }
            strategy_label = f"RSI+MACD (lookback={req.rsi_lookback})"
        else:
            from src.strategy.rsi_strategy import generate_signals
            strategy_fn     = generate_signals
            strategy_kwargs = {}
            strategy_label  = "RSI"

        result = run_backtest(
            ticker=req.ticker,
            df=df,
            initial_capital=req.capital,
            rsi_period=req.rsi_period,
            oversold=req.oversold,
            overbought=req.overbought,
            strategy_fn=strategy_fn,
            strategy_kwargs=strategy_kwargs,
        )

        chart_bytes = render_chart_bytes(result, candle_label=candle_label, strategy_label=strategy_label)
        chart_b64   = base64.b64encode(chart_bytes).decode()

        trades = [
            {
                "date":       t.date,
                "action":     t.action,
                "price":      t.price,
                "shares":     t.shares,
                "amount":     t.amount,
                "commission": t.commission,
                "rsi":        t.rsi,
            }
            for t in result.trades
        ]

        return {
            "ticker":          result.ticker.upper(),
            "candle_label":    candle_label,
            "strategy_label":  strategy_label,
            "period_start":    df.index[0].strftime("%Y-%m-%d"),
            "period_end":      df.index[-1].strftime("%Y-%m-%d"),
            "initial_capital": result.initial_capital,
            "final_capital":   result.final_capital,
            "total_profit":    result.total_profit,
            "return_rate":     result.return_rate,
            "total_trades":    result.total_trades,
            "win_trades":      result.win_trades,
            "lose_trades":     result.lose_trades,
            "win_rate":        result.win_rate,
            "max_drawdown":    result.max_drawdown,
            "trades":          trades,
            "chart_png":       chart_b64,
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
