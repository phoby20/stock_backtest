class Config:
    RSI_PERIOD = 14
    RSI_OVERSOLD = 30
    RSI_OVERBOUGHT = 70

    DATA_PERIOD = "5y"
    DEFAULT_CAPITAL = 10_000_000  # 기본 자본금 (원)

    # 실시간 감시 주기 (초)
    MONITOR_INTERVAL = 300  # 5분

    # 거래 수수료 (%)
    COMMISSION_RATE = 0.0015  # 0.15%

    # 매수 시 자본금 사용 비율
    BUY_RATIO = 1.0  # 전액 투자
