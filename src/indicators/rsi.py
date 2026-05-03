import pandas as pd
import numpy as np


def calculate_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
    """
    Wilder's EMA 방식으로 RSI 계산.
    초기 평균은 단순평균(SMA), 이후는 지수이동평균(EMA) 사용.
    """
    delta = prices.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    # Wilder's smoothing: alpha = 1/period
    avg_gain = gain.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()

    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    rsi.name = "RSI"
    return rsi


def get_rsi_signal(rsi_value: float, oversold: float = 30, overbought: float = 70) -> str:
    """RSI 값에 따른 신호 반환"""
    if rsi_value <= oversold:
        return "BUY"
    elif rsi_value >= overbought:
        return "SELL"
    return "HOLD"
