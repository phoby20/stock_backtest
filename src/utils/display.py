from tabulate import tabulate
from colorama import Fore, Style, init
from src.backtest.engine import BacktestResult

init(autoreset=True)


def print_backtest_result(result: BacktestResult, candle_label: str = "일봉", strategy_label: str = "RSI"):
    print(f"\n{'='*65}")
    print(f"  백테스트 결과 — {Fore.CYAN}{result.ticker}{Style.RESET_ALL}  [{candle_label} / {strategy_label}]")
    print(f"{'='*65}")

    profit_color = Fore.GREEN if result.total_profit >= 0 else Fore.RED
    rate_color = Fore.GREEN if result.return_rate >= 0 else Fore.RED

    summary = [
        ["초기 자본금", f"{result.initial_capital:,.0f}"],
        ["최종 자산", f"{result.final_capital:,.0f}"],
        ["총 수익금", f"{profit_color}{result.total_profit:+,.0f}{Style.RESET_ALL}"],
        ["수익률", f"{rate_color}{result.return_rate:+.2f}%{Style.RESET_ALL}"],
        ["총 거래 횟수", f"{result.total_trades}회"],
        ["승리 거래", f"{result.win_trades}회"],
        ["패배 거래", f"{result.lose_trades}회"],
        ["승률", f"{result.win_rate:.1f}%"],
        ["최대 낙폭 (MDD)", f"{result.max_drawdown:.2f}%"],
    ]
    print(tabulate(summary, headers=["항목", "값"], tablefmt="simple"))

    if result.trades:
        print(f"\n{'─'*65}")
        print("  거래 내역")
        print(f"{'─'*65}")
        rows = []
        for t in result.trades:
            action_color = Fore.GREEN if "BUY" in t.action else Fore.RED
            rows.append([
                t.date,
                f"{action_color}{t.action}{Style.RESET_ALL}",
                f"{t.price:,.4f}",
                f"{t.amount:,.0f}",
                f"{t.rsi:.2f}",
                f"{t.commission:,.0f}",
            ])
        print(tabulate(
            rows,
            headers=["날짜", "구분", "가격", "거래금액", "RSI", "수수료"],
            tablefmt="simple",
        ))

    print(f"{'='*65}\n")
