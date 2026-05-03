import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

# yfinance 분봉별 최대 수집 가능 기간
INTERVAL_MAX_PERIOD = {
    "1m":  "7d",
    "5m":  "60d",
    "15m": "60d",
    "30m": "60d",
    "1h":  "730d",
    "1d":  "5y",
}

INTERVAL_LABEL = {
    "1m":  "1분봉",
    "5m":  "5분봉",
    "15m": "15분봉",
    "30m": "30분봉",
    "1h":  "1시간봉",
    "1d":  "일봉",
}


def fetch_historical_data(ticker: str, period: str = "5y", interval: str = "1d", custom_period: str = None) -> pd.DataFrame:
    """OHLCV 데이터 수집 (일봉 및 분봉 지원)"""
    max_period = INTERVAL_MAX_PERIOD.get(interval, period)
    if custom_period:
        # 사용자 지정 기간이 최대치를 초과하면 자동으로 max_period 사용
        period = custom_period
    elif interval != "1d":
        period = max_period

    stock = yf.Ticker(ticker)
    df = stock.history(period=period, interval=interval)

    if df.empty:
        raise ValueError(f"'{ticker}' 종목의 데이터를 가져올 수 없습니다. 티커를 확인하세요.")

    df.index = pd.to_datetime(df.index).tz_localize(None)
    df = df[["Open", "High", "Low", "Close", "Volume"]]
    df.dropna(inplace=True)
    return df


def fetch_ticker_info(ticker: str) -> dict:
    """종목 기본 정보 조회"""
    stock = yf.Ticker(ticker)
    info = stock.info
    return {
        "name": info.get("longName", info.get("shortName", ticker)),
        "currency": info.get("currency", "USD"),
        "exchange": info.get("exchange", "Unknown"),
        "sector": info.get("sector", "Unknown"),
        "current_price": info.get("regularMarketPrice", info.get("currentPrice", 0)),
    }


def fetch_latest_price(ticker: str) -> float:
    """현재가 조회 (실시간 감시용)"""
    stock = yf.Ticker(ticker)
    # 최근 1일 데이터에서 마지막 종가 사용
    df = stock.history(period="1d", interval="1m")
    if df.empty:
        df = stock.history(period="2d")
    if df.empty:
        raise ValueError(f"'{ticker}' 현재가를 가져올 수 없습니다.")
    return float(df["Close"].iloc[-1])


def fetch_intraday_data(ticker: str, interval: str = "5m", period: str = "1d") -> pd.DataFrame:
    """장중 데이터 수집 (실시간 감시용)"""
    stock = yf.Ticker(ticker)
    df = stock.history(period=period, interval=interval)
    if df.empty:
        raise ValueError(f"'{ticker}' 장중 데이터를 가져올 수 없습니다.")
    df.index = pd.to_datetime(df.index).tz_localize(None)
    return df[["Open", "High", "Low", "Close", "Volume"]]
