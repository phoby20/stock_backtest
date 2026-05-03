import pandas as pd


def calculate_macd(
    prices: pd.Series,
    fast: int = 12,
    slow: int = 26,
    signal: int = 9,
) -> tuple[pd.Series, pd.Series, pd.Series]:
    """
    MACD 계산.
    반환: (macd_line, signal_line, histogram)
    """
    ema_fast = prices.ewm(span=fast, adjust=False).mean()
    ema_slow = prices.ewm(span=slow, adjust=False).mean()

    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line

    macd_line.name = "MACD"
    signal_line.name = "MACD_Signal"
    histogram.name = "MACD_Hist"

    return macd_line, signal_line, histogram


def detect_golden_cross(macd_line: pd.Series, signal_line: pd.Series) -> pd.Series:
    """MACD 골든크로스: MACD가 Signal을 아래→위로 돌파한 봉"""
    prev_below = macd_line.shift(1) < signal_line.shift(1)
    curr_above = macd_line >= signal_line
    return prev_below & curr_above


def detect_dead_cross(macd_line: pd.Series, signal_line: pd.Series) -> pd.Series:
    """MACD 데드크로스: MACD가 Signal을 위→아래로 돌파한 봉"""
    prev_above = macd_line.shift(1) > signal_line.shift(1)
    curr_below = macd_line <= signal_line
    return prev_above & curr_below
