import time
from datetime import datetime
from colorama import Fore, Style, init
from src.data.fetcher import fetch_intraday_data, fetch_historical_data
from src.indicators.rsi import calculate_rsi, get_rsi_signal
from config import Config

init(autoreset=True)


def _print_status(ticker: str, price: float, rsi: float, signal: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    signal_color = {
        "BUY": Fore.GREEN,
        "SELL": Fore.RED,
        "HOLD": Fore.YELLOW,
    }.get(signal, Fore.WHITE)

    print(f"[{ts}] {Fore.CYAN}{ticker}{Style.RESET_ALL} | "
          f"현재가: {price:,.2f} | "
          f"RSI: {rsi:.2f} | "
          f"신호: {signal_color}{signal}{Style.RESET_ALL}")


def start_monitor(
    ticker: str,
    interval: int = Config.MONITOR_INTERVAL,
    rsi_period: int = Config.RSI_PERIOD,
    oversold: float = Config.RSI_OVERSOLD,
    overbought: float = Config.RSI_OVERBOUGHT,
):
    """
    실시간 RSI 감시 루프.
    RSI 계산을 위해 과거 데이터(60일)를 기반 데이터로 사용하고,
    주기마다 최신 가격을 추가하여 RSI를 갱신합니다.
    """
    print(f"\n{'='*60}")
    print(f"  실시간 감시 시작: {Fore.CYAN}{ticker}{Style.RESET_ALL}")
    print(f"  RSI 기간: {rsi_period} | 매수: RSI≤{oversold} | 매도: RSI≥{overbought}")
    print(f"  갱신 주기: {interval}초 | 종료: Ctrl+C")
    print(f"{'='*60}\n")

    # 기반 데이터: 최근 60일 일봉 (RSI 계산 정확도 확보)
    base_df = fetch_historical_data(ticker, period="60d")
    prices = base_df["Close"].copy()

    try:
        while True:
            try:
                # 장중 데이터로 현재가 갱신
                intraday = fetch_intraday_data(ticker, interval="5m", period="1d")
                latest_price = float(intraday["Close"].iloc[-1])

                # 최신 가격을 시리즈에 추가하여 RSI 계산
                latest_time = intraday.index[-1]
                prices[latest_time] = latest_price
                prices = prices[~prices.index.duplicated(keep="last")].sort_index()

                rsi_series = calculate_rsi(prices, period=rsi_period)
                latest_rsi = float(rsi_series.iloc[-1])
                signal = get_rsi_signal(latest_rsi, oversold=oversold, overbought=overbought)

                _print_status(ticker, latest_price, latest_rsi, signal)

                if signal == "BUY":
                    print(f"  {Fore.GREEN}>>> 매수 신호 발생! RSI({latest_rsi:.2f}) ≤ {oversold} <<<{Style.RESET_ALL}")
                elif signal == "SELL":
                    print(f"  {Fore.RED}>>> 매도 신호 발생! RSI({latest_rsi:.2f}) ≥ {overbought} <<<{Style.RESET_ALL}")

            except Exception as e:
                print(f"  {Fore.RED}데이터 수집 오류: {e}{Style.RESET_ALL}")

            time.sleep(interval)

    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}감시를 종료합니다.{Style.RESET_ALL}")
