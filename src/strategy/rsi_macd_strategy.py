import pandas as pd
from src.indicators.rsi import calculate_rsi
from src.indicators.macd import calculate_macd, detect_golden_cross, detect_dead_cross


def generate_signals(
    df: pd.DataFrame,
    rsi_period: int = 14,
    oversold: float = 30,
    overbought: float = 70,
    macd_fast: int = 12,
    macd_slow: int = 26,
    macd_signal: int = 9,
    rsi_lookback: int = 5,   # RSI 조건을 기억할 봉 수
) -> pd.DataFrame:
    """
    RSI + MACD 복합 전략 신호 생성.

    매수: 최근 N봉 안에 RSI ≤ oversold 구간 진입한 적 있음
          AND 현재 봉에서 MACD 골든크로스 발생
    매도: 최근 N봉 안에 RSI ≥ overbought 구간 진입한 적 있음
          AND 현재 봉에서 MACD 데드크로스 발생

    MACD는 RSI보다 후행하므로 RSI 조건을 lookback 창으로 기억해 두고,
    골든/데드크로스 발생 시점에 매매합니다.
    """
    result = df.copy()

    # RSI 계산
    result["RSI"] = calculate_rsi(result["Close"], period=rsi_period)

    # MACD 계산
    macd_line, signal_line, histogram = calculate_macd(
        result["Close"], fast=macd_fast, slow=macd_slow, signal=macd_signal
    )
    result["MACD"]        = macd_line
    result["MACD_Signal"] = signal_line
    result["MACD_Hist"]   = histogram

    # 크로스 감지
    golden = detect_golden_cross(result["MACD"], result["MACD_Signal"])
    dead   = detect_dead_cross(result["MACD"],   result["MACD_Signal"])

    # ── RSI 조건: lookback 창 안에 조건을 만족한 적 있는지 ──
    # 최근 N봉 안에 RSI ≤ oversold 였던 적 있음 (rolling min)
    rsi_was_oversold   = result["RSI"].rolling(rsi_lookback).min() <= oversold
    # 최근 N봉 안에 RSI ≥ overbought 였던 적 있음 (rolling max)
    rsi_was_overbought = result["RSI"].rolling(rsi_lookback).max() >= overbought

    # RSI 꺾임: 현재 봉 RSI가 직전보다 낮음 (고점에서 하락 전환)
    rsi_falling = result["RSI"] < result["RSI"].shift(1)

    # ── 신호 생성 ──────────────────────────────────────────
    result["Signal"] = "HOLD"

    # 매수: 최근 N봉 안에 RSI 과매도 진입 + 지금 골든크로스
    buy_cond  = rsi_was_oversold & golden

    # 매도: 최근 N봉 안에 RSI 과매수 진입 + RSI 꺾임 + 지금 데드크로스
    sell_cond = rsi_was_overbought & rsi_falling & dead

    result.loc[buy_cond,  "Signal"] = "BUY"
    result.loc[sell_cond, "Signal"] = "SELL"

    return result
