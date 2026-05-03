# Vercel Python Serverless Function entry point
# Vercel이 이 파일을 /api/backtest 엔드포인트로 자동 인식합니다.
import matplotlib
matplotlib.use("Agg")  # 디스플레이 없는 환경에서 PNG 렌더링

from api.server import app  # FastAPI app 공유 (로직 중복 없음)
from mangum import Mangum

handler = Mangum(app, lifespan="off")
