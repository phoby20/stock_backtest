# /api/backtest — Next.js app/api/backtest/route.ts가 우선 처리하므로
# 이 Python 함수는 실제로 호출되지 않습니다.
# 하지만 Vercel이 import를 시도하므로 빈 handler로 대응합니다.
import matplotlib
matplotlib.use("Agg")

from api.py_backtest import handler  # noqa: F401
