import pandas as pd
import numpy as np
from dataclasses import dataclass, field
from typing import List, Callable, Optional


@dataclass
class Trade:
    date: str
    action: str       # BUY or SELL
    price: float
    shares: float
    amount: float     # 거래 금액 (수수료 포함)
    commission: float
    rsi: float


@dataclass
class BacktestResult:
    ticker: str
    initial_capital: float
    final_capital: float
    trades: List[Trade] = field(default_factory=list)
    signals_df: pd.DataFrame = field(default_factory=pd.DataFrame)

    @property
    def total_profit(self) -> float:
        return self.final_capital - self.initial_capital

    @property
    def return_rate(self) -> float:
        return (self.total_profit / self.initial_capital) * 100

    @property
    def total_trades(self) -> int:
        return len([t for t in self.trades if t.action == "SELL"])

    @property
    def win_trades(self) -> int:
        profits = self._per_trade_profits()
        return sum(1 for p in profits if p > 0)

    @property
    def lose_trades(self) -> int:
        profits = self._per_trade_profits()
        return sum(1 for p in profits if p <= 0)

    @property
    def win_rate(self) -> float:
        if self.total_trades == 0:
            return 0.0
        return (self.win_trades / self.total_trades) * 100

    @property
    def max_drawdown(self) -> float:
        if not self.trades:
            return 0.0
        portfolio_values = [t.amount for t in self.trades]
        if len(portfolio_values) < 2:
            return 0.0
        peak = portfolio_values[0]
        max_dd = 0.0
        for v in portfolio_values:
            if v > peak:
                peak = v
            dd = (peak - v) / peak * 100
            if dd > max_dd:
                max_dd = dd
        return max_dd

    def _per_trade_profits(self) -> List[float]:
        profits = []
        buy_price = None
        buy_amount = None
        for t in self.trades:
            if t.action == "BUY":
                buy_price = t.price
                buy_amount = t.amount
            elif t.action == "SELL" and buy_price is not None:
                profit = t.amount - buy_amount
                profits.append(profit)
                buy_price = None
                buy_amount = None
        return profits


def run_backtest(
    ticker: str,
    df: pd.DataFrame,
    initial_capital: float = 10_000_000,
    rsi_period: int = 14,
    oversold: float = 30,
    overbought: float = 70,
    commission_rate: float = 0.0015,
    strategy_fn: Optional[Callable] = None,
    strategy_kwargs: Optional[dict] = None,
) -> BacktestResult:
    """RSI / RSI+MACD 전략 백테스트 실행"""
    if strategy_fn is None:
        from src.strategy.rsi_strategy import generate_signals as default_fn
        strategy_fn = default_fn

    kwargs = strategy_kwargs or {}
    signals_df = strategy_fn(df, rsi_period=rsi_period,
                             oversold=oversold, overbought=overbought, **kwargs)
    signals_df = signals_df.dropna(subset=["RSI"])

    capital = initial_capital
    shares = 0.0
    trades: List[Trade] = []
    position = False  # 현재 포지션 보유 여부

    for date, row in signals_df.iterrows():
        signal = row["Signal"]
        price = row["Close"]
        rsi = row["RSI"]

        if signal == "BUY" and not position and capital > 0:
            commission = capital * commission_rate
            investable = capital - commission
            bought_shares = investable / price
            shares = bought_shares
            trade_amount = capital
            capital = 0.0
            position = True
            trades.append(Trade(
                date=date.strftime("%Y-%m-%d %H:%M") if date.hour or date.minute else str(date.date()),
                action="BUY",
                price=round(price, 4),
                shares=round(shares, 6),
                amount=round(trade_amount, 2),
                commission=round(commission, 2),
                rsi=round(rsi, 2),
            ))

        elif signal == "SELL" and position and shares > 0:
            gross = shares * price
            commission = gross * commission_rate
            net = gross - commission
            capital = net
            trade_amount = net
            shares = 0.0
            position = False
            trades.append(Trade(
                date=date.strftime("%Y-%m-%d %H:%M") if date.hour or date.minute else str(date.date()),
                action="SELL",
                price=round(price, 4),
                shares=round(shares, 6),
                amount=round(trade_amount, 2),
                commission=round(commission, 2),
                rsi=round(rsi, 2),
            ))

    # 기간 종료 시 포지션 강제 청산
    if position and shares > 0:
        last_price = signals_df["Close"].iloc[-1]
        last_rsi = signals_df["RSI"].iloc[-1]
        gross = shares * last_price
        commission = gross * commission_rate
        capital = gross - commission
        trades.append(Trade(
            date=signals_df.index[-1].strftime("%Y-%m-%d %H:%M") if signals_df.index[-1].hour or signals_df.index[-1].minute else str(signals_df.index[-1].date()),
            action="SELL(종료)",
            price=round(last_price, 4),
            shares=round(shares, 6),
            amount=round(capital, 2),
            commission=round(commission, 2),
            rsi=round(last_rsi, 2),
        ))

    return BacktestResult(
        ticker=ticker,
        initial_capital=initial_capital,
        final_capital=round(capital, 2),
        trades=trades,
        signals_df=signals_df,
    )
