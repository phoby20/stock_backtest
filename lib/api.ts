const PY_ENDPOINT = "/api/py_backtest"
const TS_ENDPOINT = "/api/backtest"

export interface BacktestRequest {
  ticker:        string
  candle:        string
  capital:       number
  strategy:      string
  rsi_period:    number
  oversold:      number
  overbought:    number
  macd_fast:     number
  macd_slow:     number
  macd_signal:   number
  rsi_lookback:  number
  custom_period?: string
}

export interface Trade {
  date:       string
  action:     string
  price:      number
  shares:     number
  amount:     number
  commission: number
  rsi:        number
}

export interface ChartPoint {
  date:       string
  close:      number
  rsi:        number | null
  macd:       number
  macdSignal: number
  macdHist:   number
  portfolio:  number
  signal:     string
}

export interface BacktestResponse {
  ticker:          string
  candle_label:    string
  strategy_label:  string
  period_start:    string
  period_end:      string
  initial_capital: number
  final_capital:   number
  total_profit:    number
  return_rate:     number
  total_trades:    number
  win_trades:      number
  lose_trades:     number
  win_rate:        number
  max_drawdown:    number
  trades:          Trade[]
  chart_png:       string
  chart_data?:     ChartPoint[]
}

export async function runBacktest(req: BacktestRequest): Promise<BacktestResponse> {
  const body = JSON.stringify(req)
  const opts = { method: "POST", headers: { "Content-Type": "application/json" }, body }

  // Python(matplotlib) 엔드포인트 우선 시도 → 실패 시 Next.js fallback
  const pyRes = await fetch(PY_ENDPOINT, opts).catch(() => null)
  if (pyRes?.ok) return pyRes.json()

  const res = await fetch(TS_ENDPOINT, opts)
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "서버 오류" }))
    throw new Error(err.detail ?? "백테스트 실패")
  }
  return res.json()
}
