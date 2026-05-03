import pandas as pd
from src.indicators.rsi import calculate_rsi


def generate_signals(df: pd.DataFrame, rsi_period: int = 14,
                     oversold: float = 30, overbought: float = 70) -> pd.DataFrame:
    """
    RSI 기반 매수/매도 신호 생성.
    RSI가 oversold 아래로 내려갈 때 BUY,
    RSI가 overbought 위로 올라갈 때 SELL 신호 발생.
    """
    result = df.copy()
    result["RSI"] = calculate_rsi(result["Close"], period=rsi_period)

    result["Signal"] = "HOLD"
    # RSI가 과매도 구간에 진입하면 BUY
    result.loc[result["RSI"] <= oversold, "Signal"] = "BUY"
    # RSI가 과매수 구간에 진입하면 SELL
    result.loc[result["RSI"] >= overbought, "Signal"] = "SELL"

    return result
