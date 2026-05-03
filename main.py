#!/usr/bin/env python3
"""
RSI 기반 주식 자동 거래 프로그램
  - backtest: 과거 데이터로 백테스트 (일봉/분봉 선택 가능)
  - monitor : 실시간 RSI 감시 (신호 알림)

사용 예시:
  python main.py backtest --ticker AAPL
  python main.py backtest --ticker TSLA --candle 1h --capital 1000
  python main.py backtest --ticker AAPL --candle 5m
  python main.py monitor  --ticker AAPL --interval 60
  python main.py monitor  --ticker 005930.KS
"""

import argparse
import sys
from colorama import Fore, Style, init

init(autoreset=True)


def cmd_backtest(args):
    from src.data.fetcher import fetch_historical_data, fetch_ticker_info, INTERVAL_LABEL, INTERVAL_MAX_PERIOD
    from src.backtest.engine import run_backtest
    from src.utils.display import print_backtest_result

    candle = args.candle
    label = INTERVAL_LABEL.get(candle, candle)
    max_period = INTERVAL_MAX_PERIOD.get(candle, "5y")

    print(f"\n{Fore.CYAN}[백테스트]{Style.RESET_ALL} {args.ticker} 데이터 수집 중... ({label})", flush=True)

    try:
        info = fetch_ticker_info(args.ticker)
        print(f"  종목명: {info['name']} | 거래소: {info['exchange']} | 통화: {info['currency']}")

        custom_period = args.period if args.period else None
        df = fetch_historical_data(args.ticker, interval=candle, custom_period=custom_period)
        bar_count = len(df)
        period_label = custom_period if custom_period else max_period
        print(f"  봉 단위: {label} | 데이터 기간: {period_label}")
        print(f"  수집 범위: {df.index[0].strftime('%Y-%m-%d %H:%M')} ~ {df.index[-1].strftime('%Y-%m-%d %H:%M')} ({bar_count:,}봉)")
    except ValueError as e:
        print(f"{Fore.RED}오류: {e}{Style.RESET_ALL}")
        sys.exit(1)

    # 봉 단위별 자동 lookback 설정
    auto_lookback = {"1m": 10, "5m": 10, "15m": 10, "30m": 10, "1h": 12, "1d": 20}
    lookback = auto_lookback.get(candle, 10)

    # 전략 선택
    if args.strategy == "rsi-macd":
        from src.strategy.rsi_macd_strategy import generate_signals as strategy_fn
        strategy_kwargs = {
            "macd_fast":    args.macd_fast,
            "macd_slow":    args.macd_slow,
            "macd_signal":  args.macd_signal,
            "rsi_lookback": lookback,
        }
        strategy_label = f"RSI({args.rsi_period}) + MACD({args.macd_fast}/{args.macd_slow}/{args.macd_signal})"
    else:
        from src.strategy.rsi_strategy import generate_signals as strategy_fn
        strategy_kwargs = {}
        strategy_label = f"RSI({args.rsi_period})"

    print(f"  전략: {strategy_label} | RSI lookback: {lookback}봉")
    print(f"  RSI 매수 기준: ≤{args.oversold} | 매도 기준: ≥{args.overbought}")
    print(f"  초기 자본금: {args.capital:,.0f} | 수수료: {args.commission * 100:.2f}%\n")

    result = run_backtest(
        ticker=args.ticker,
        df=df,
        initial_capital=args.capital,
        rsi_period=args.rsi_period,
        oversold=args.oversold,
        overbought=args.overbought,
        commission_rate=args.commission,
        strategy_fn=strategy_fn,
        strategy_kwargs=strategy_kwargs,
    )

    print_backtest_result(result, candle_label=label, strategy_label=strategy_label)

    if args.chart:
        from src.utils.chart import plot_backtest
        import os
        save_path = os.path.join(
            os.path.dirname(__file__),
            f"{args.ticker}_{candle}_{args.strategy}_chart.png"
        )
        print(f"\n{Fore.CYAN}[차트]{Style.RESET_ALL} 그래프 생성 중...")
        plot_backtest(result, candle_label=label, strategy_label=strategy_label, save_path=save_path)


def cmd_monitor(args):
    from src.data.fetcher import fetch_ticker_info
    from src.trading.monitor import start_monitor

    try:
        info = fetch_ticker_info(args.ticker)
        print(f"\n종목: {info['name']} ({args.ticker}) | 현재가: {info['current_price']:,.2f} {info['currency']}")
    except Exception as e:
        print(f"{Fore.YELLOW}종목 정보 조회 실패 (계속 진행): {e}{Style.RESET_ALL}")

    start_monitor(
        ticker=args.ticker,
        interval=args.interval,
        rsi_period=args.rsi_period,
        oversold=args.oversold,
        overbought=args.overbought,
    )


def cmd_trade(args):
    """키움 OpenAPI+ 실시간 자동매매 (Windows 전용)"""
    try:
        from src.trading.live_trader import LiveTrader
    except ImportError as e:
        print(f"{Fore.RED}오류: {e}")
        print(f"PyQt5 설치 필요 → pip install PyQt5{Style.RESET_ALL}")
        sys.exit(1)

    trader = LiveTrader(
        ticker=args.ticker,
        account=args.account,
        rsi_period=args.rsi_period,
        oversold=args.oversold,
        overbought=args.overbought,
        macd_fast=args.macd_fast,
        macd_slow=args.macd_slow,
        macd_signal=args.macd_signal,
        buy_ratio=args.buy_ratio,
        paper=args.paper,
    )
    trader.run()


def main():
    parser = argparse.ArgumentParser(
        description="RSI+MACD 주식 자동 거래 프로그램",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
  python main.py backtest --ticker 005930.KS --candle 1d --capital 10000000
  python main.py backtest --ticker AAPL --candle 5m --strategy rsi-macd --chart
  python main.py monitor  --ticker 005930.KS --interval 60
  python main.py trade    --ticker 005930 --account 1234567890 --paper
  python main.py trade    --ticker 005930 --account 1234567890
        """,
    )

    sub = parser.add_subparsers(dest="command", required=True)

    # ── backtest 서브커맨드 ──────────────────────────────────
    bt = sub.add_parser("backtest", help="과거 데이터로 백테스트 실행 (일봉/분봉 선택 가능)")
    bt.add_argument("--ticker",     required=True,  help="종목 코드 (예: AAPL, 005930.KS)")
    bt.add_argument("--candle",     default="1h",
                    choices=["1m", "5m", "15m", "30m", "1h", "1d"],
                    help="봉 단위 (기본: 1h=시간봉 / 1m=7일 5m·15m·30m=60일 1h=2년 1d=5년)")
    bt.add_argument("--capital",    type=float, default=10_000_000, help="초기 자본금 (기본: 10,000,000)")
    bt.add_argument("--rsi-period", type=int,   default=14,         help="RSI 기간 (기본: 14)")
    bt.add_argument("--oversold",   type=float, default=30.0,       help="매수 RSI 기준 (기본: 30)")
    bt.add_argument("--overbought", type=float, default=70.0,       help="매도 RSI 기준 (기본: 70)")
    bt.add_argument("--commission",   type=float, default=0.0015,   help="수수료율 (기본: 0.0015 = 0.15%%)")
    bt.add_argument("--strategy",     default="rsi",
                    choices=["rsi", "rsi-macd"],
                    help="전략 선택: rsi (기본) / rsi-macd")
    bt.add_argument("--macd-fast",    type=int,   default=12,       help="MACD 단기 EMA (기본: 12)")
    bt.add_argument("--macd-slow",    type=int,   default=26,       help="MACD 장기 EMA (기본: 26)")
    bt.add_argument("--macd-signal",  type=int,   default=9,        help="MACD 시그널 EMA (기본: 9)")
    bt.add_argument("--period",       default=None,                 help="데이터 기간 지정 (예: 7d, 14d, 30d, 60d, 1y, 5y)")
    bt.add_argument("--chart",        action="store_true",          help="백테스트 결과 그래프 출력")
    bt.set_defaults(func=cmd_backtest)

    # ── monitor 서브커맨드 ───────────────────────────────────
    mo = sub.add_parser("monitor", help="실시간 RSI 감시 및 신호 알림 (Yahoo Finance)")
    mo.add_argument("--ticker",     required=True,  help="종목 코드 (예: AAPL, 005930.KS)")
    mo.add_argument("--interval",   type=int,   default=300,  help="갱신 주기 초 (기본: 300 = 5분)")
    mo.add_argument("--rsi-period", type=int,   default=14,   help="RSI 기간 (기본: 14)")
    mo.add_argument("--oversold",   type=float, default=30.0, help="매수 RSI 기준 (기본: 30)")
    mo.add_argument("--overbought", type=float, default=70.0, help="매도 RSI 기준 (기본: 70)")
    mo.set_defaults(func=cmd_monitor)

    # ── trade 서브커맨드 (키움 OpenAPI+ / Windows 전용) ───────
    tr = sub.add_parser("trade", help="키움 OpenAPI+ 실시간 자동매매 [Windows 전용]")
    tr.add_argument("--ticker",      required=True,  help="종목코드 (예: 005930)")
    tr.add_argument("--account",     required=True,  help="계좌번호 (예: 1234567890)")
    tr.add_argument("--rsi-period",  type=int,   default=14,   help="RSI 기간 (기본: 14)")
    tr.add_argument("--oversold",    type=float, default=30.0, help="매수 RSI 기준 (기본: 30)")
    tr.add_argument("--overbought",  type=float, default=70.0, help="매도 RSI 기준 (기본: 70)")
    tr.add_argument("--macd-fast",   type=int,   default=12,   help="MACD 단기 EMA (기본: 12)")
    tr.add_argument("--macd-slow",   type=int,   default=26,   help="MACD 장기 EMA (기본: 26)")
    tr.add_argument("--macd-signal", type=int,   default=9,    help="MACD 시그널 (기본: 9)")
    tr.add_argument("--buy-ratio",   type=float, default=1.0,  help="매수 시 예수금 사용 비율 (기본: 1.0 = 전액)")
    tr.add_argument("--paper",       action="store_true",      help="모의매매 모드 (실제 주문 미전송)")
    tr.set_defaults(func=cmd_trade)

    args = parser.parse_args()
    # argparse의 dest 이름은 '-'를 '_'로 자동 변환하므로 그대로 사용
    args.func(args)


if __name__ == "__main__":
    main()
