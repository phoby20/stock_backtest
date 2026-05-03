import { NextRequest, NextResponse } from 'next/server'
import YahooFinance from 'yahoo-finance2'
import { auth } from '@clerk/nextjs/server'
import { getDb } from '@/lib/db'

const yahooFinance = new YahooFinance()

export const maxDuration = 30

// ── 인메모리 캐시 (5분 TTL) ───────────────────────────────────

interface CacheEntry { data: { date: string; close: number }[]; expiresAt: number }
const _cache = new Map<string, CacheEntry>()

function getCached(key: string) {
  const entry = _cache.get(key)
  if (!entry || Date.now() > entry.expiresAt) { _cache.delete(key); return null }
  return entry.data
}
function setCached(key: string, data: { date: string; close: number }[]) {
  _cache.set(key, { data, expiresAt: Date.now() + 5 * 60 * 1000 })
}

// ── Constants ─────────────────────────────────────────────────

const CANDLE_META: Record<string, { label: string; maxPeriod: string; autoLookback: number }> = {
  '1m':  { label: '1분봉',   maxPeriod: '7d',   autoLookback: 10 },
  '5m':  { label: '5분봉',   maxPeriod: '60d',  autoLookback: 10 },
  '15m': { label: '15분봉',  maxPeriod: '60d',  autoLookback: 10 },
  '30m': { label: '30분봉',  maxPeriod: '60d',  autoLookback: 10 },
  '1h':  { label: '1시간봉', maxPeriod: '730d', autoLookback: 12 },
  '1d':  { label: '일봉',    maxPeriod: '5y',   autoLookback: 20 },
}

// ── Types ─────────────────────────────────────────────────────

interface OHLCVRow { date: Date; close: number }

interface Trade {
  date: string
  action: string
  price: number
  shares: number
  amount: number
  commission: number
  rsi: number
}

// ── Helpers ───────────────────────────────────────────────────

function periodToStart(period: string): Date {
  const now = new Date()
  const m = period.match(/^(\d+)(d|y)$/)
  if (!m) return new Date(now.getTime() - 365 * 86400_000)
  const n = parseInt(m[1])
  return m[2] === 'y'
    ? new Date(now.getTime() - n * 365 * 86400_000)
    : new Date(now.getTime() - n * 86400_000)
}

function round(v: number, dp: number) { return Math.round(v * 10 ** dp) / 10 ** dp }
function fmtDate(d: Date)             { return d.toISOString().split('T')[0] }

// ── Indicators ────────────────────────────────────────────────

/** Wilder's EMA RSI — matches pandas ewm(alpha=1/period, min_periods=period, adjust=False) */
function calcRSI(closes: number[], period: number): (number | null)[] {
  const rsi: (number | null)[] = new Array(closes.length).fill(null)
  const alpha = 1 / period
  let avgGain = 0, avgLoss = 0

  for (let i = 1; i < closes.length; i++) {
    const d = closes[i] - closes[i - 1]
    const g = d > 0 ? d : 0
    const l = d < 0 ? -d : 0
    if (i === 1) { avgGain = g; avgLoss = l }
    else         { avgGain = alpha * g + (1 - alpha) * avgGain; avgLoss = alpha * l + (1 - alpha) * avgLoss }
    if (i >= period) {
      const rs = avgLoss === 0 ? Infinity : avgGain / avgLoss
      rsi[i] = 100 - 100 / (1 + rs)
    }
  }
  return rsi
}

/** Standard EMA — matches pandas ewm(span=n, adjust=False) */
function emaSpan(values: number[], span: number): number[] {
  const alpha = 2 / (span + 1)
  const out = new Array(values.length).fill(NaN)
  out[0] = values[0]
  for (let i = 1; i < values.length; i++) out[i] = alpha * values[i] + (1 - alpha) * out[i - 1]
  return out
}

function calcMACD(closes: number[], fast: number, slow: number, sig: number) {
  const macd    = emaSpan(closes, fast).map((f, i) => f - emaSpan(closes, slow)[i])
  const signal  = emaSpan(macd, sig)
  const hist    = macd.map((m, i) => m - signal[i])
  return { macd, signal, hist }
}

// ── Strategy ──────────────────────────────────────────────────

function generateSignalsRsiMacd(
  rsi: (number | null)[],
  macd: number[], sig: number[],
  oversold: number, overbought: number, lookback: number,
): string[] {
  const n = rsi.length
  const out = new Array<string>(n).fill('HOLD')

  for (let i = 1; i < n; i++) {
    const golden = macd[i - 1] < sig[i - 1] && macd[i] >= sig[i]
    const dead   = macd[i - 1] > sig[i - 1] && macd[i] <= sig[i]

    let wasOver = false, wasUnder = false
    for (let j = Math.max(0, i - lookback + 1); j <= i; j++) {
      const r = rsi[j]
      if (r !== null) {
        if (r <= oversold)   wasUnder = true
        if (r >= overbought) wasOver  = true
      }
    }

    const falling = rsi[i] !== null && rsi[i - 1] !== null && (rsi[i] as number) < (rsi[i - 1] as number)
    if (wasUnder && golden)          out[i] = 'BUY'
    else if (wasOver && falling && dead) out[i] = 'SELL'
  }
  return out
}

// ── Backtest engine ───────────────────────────────────────────

function runBacktest(
  data: OHLCVRow[], rsi: (number | null)[], signals: string[],
  initialCapital: number, commissionRate = 0.0015,
) {
  let capital = initialCapital, shares = 0, position = false
  const trades: Trade[] = []
  const portfolioValues: number[] = []

  for (let i = 0; i < data.length; i++) {
    const signal = signals[i]
    const price  = data[i].close
    const date   = fmtDate(data[i].date)

    if (signal === 'BUY' && !position && capital > 0) {
      const commission = capital * commissionRate
      shares           = (capital - commission) / price
      trades.push({ date, action: 'BUY', price: round(price, 4), shares: round(shares, 6), amount: round(capital, 2), commission: round(commission, 2), rsi: round(rsi[i] ?? 0, 2) })
      capital  = 0
      position = true
    } else if (signal === 'SELL' && position && shares > 0) {
      const gross      = shares * price
      const commission = gross * commissionRate
      capital          = gross - commission
      trades.push({ date, action: 'SELL', price: round(price, 4), shares: 0, amount: round(capital, 2), commission: round(commission, 2), rsi: round(rsi[i] ?? 0, 2) })
      shares   = 0
      position = false
    }

    portfolioValues.push(capital + shares * price)
  }

  if (position && shares > 0) {
    const last       = data[data.length - 1]
    const gross      = shares * last.close
    const commission = gross * commissionRate
    capital          = gross - commission
    trades.push({ date: fmtDate(last.date), action: 'SELL(종료)', price: round(last.close, 4), shares: 0, amount: round(capital, 2), commission: round(commission, 2), rsi: round(rsi[data.length - 1] ?? 0, 2) })
    portfolioValues[portfolioValues.length - 1] = capital
  }

  return { finalCapital: round(capital, 2), trades, portfolioValues }
}

function computeStats(trades: Trade[], initialCapital: number, portfolio: number[]) {
  const profits: number[] = []
  let buyAmt: number | null = null
  for (const t of trades) {
    if (t.action === 'BUY') buyAmt = t.amount
    else if (buyAmt !== null) { profits.push(t.amount - buyAmt); buyAmt = null }
  }
  const sells = trades.filter(t => t.action.startsWith('SELL')).length
  const wins  = profits.filter(p => p > 0).length

  let peak = portfolio[0] ?? initialCapital, maxDD = 0
  for (const v of portfolio) {
    if (v > peak) peak = v
    const dd = peak > 0 ? (peak - v) / peak * 100 : 0
    if (dd > maxDD) maxDD = dd
  }

  return { totalTrades: sells, winTrades: wins, loseTrades: sells - wins, winRate: sells ? (wins / sells) * 100 : 0, maxDrawdown: maxDD }
}

// ── Route handler ─────────────────────────────────────────────

export async function POST(req: NextRequest) {
  try {
    // ── 인증 확인 ────────────────────────────────────────────
    const { userId } = await auth()
    if (!userId) {
      return NextResponse.json({ detail: '로그인이 필요합니다.' }, { status: 401 })
    }

    const {
      ticker       = 'AAPL',
      candle       = '1d',
      capital      = 10_000_000,
      strategy     = 'rsi-macd',
      rsi_period   = 14,
      oversold     = 30,
      overbought   = 70,
      macd_fast    = 12,
      macd_slow    = 26,
      macd_signal  = 9,
      rsi_lookback = 20,
      custom_period,
    } = await req.json()

    const meta      = CANDLE_META[candle] ?? { label: candle, maxPeriod: '5y', autoLookback: 20 }
    const period    = custom_period ?? meta.maxPeriod
    const startDate = periodToStart(period)

    // ── Yahoo Finance 데이터 (캐시 우선) ─────────────────────
    const cacheKey = `${ticker.toUpperCase()}:${period}:${candle}`
    const cached = getCached(cacheKey)
    let rawData: { date: string; close: number }[]

    if (cached) {
      rawData = cached
    } else {
      // chart() 는 일봉·분봉 모두 지원
      const res = await yahooFinance.chart(ticker.toUpperCase(), {
        period1:  startDate,
        period2:  new Date(),
        interval: candle as '1d' | '1h' | '30m' | '15m' | '5m' | '1m',
      })

      const quotes = res.quotes ?? []
      if (!quotes.length) {
        return NextResponse.json({ detail: `'${ticker}' 데이터를 가져올 수 없습니다.` }, { status: 400 })
      }

      rawData = quotes
        .filter((r): r is typeof r & { close: number } => r.close != null)
        .map(r => ({ date: r.date.toISOString(), close: r.close }))

      setCached(cacheKey, rawData)
    }

    const data: OHLCVRow[] = rawData.map(r => ({ date: new Date(r.date), close: r.close }))

    const closes = data.map(r => r.close)

    const rsi = calcRSI(closes, rsi_period)
    const { macd, signal: macdSig, hist } = calcMACD(closes, macd_fast, macd_slow, macd_signal)

    const signals = strategy === 'rsi-macd'
      ? generateSignalsRsiMacd(rsi, macd, macdSig, oversold, overbought, rsi_lookback)
      : data.map((_, i) => {
          const r = rsi[i]
          if (r === null) return 'HOLD'
          if (r <= oversold)   return 'BUY'
          if (r >= overbought) return 'SELL'
          return 'HOLD'
        })

    const result = runBacktest(data, rsi, signals, capital)
    const stats  = computeStats(result.trades, capital, result.portfolioValues)

    const chartData = data.map((r, i) => ({
      date:       fmtDate(r.date),
      close:      round(r.close, 4),
      rsi:        rsi[i] !== null ? round(rsi[i] as number, 2) : null,
      macd:       round(macd[i], 4),
      macdSignal: round(macdSig[i], 4),
      macdHist:   round(hist[i], 4),
      portfolio:  round(result.portfolioValues[i], 2),
      signal:     signals[i],
    }))

    const strategyLabel = strategy === 'rsi-macd'
      ? `RSI+MACD (lookback=${rsi_lookback})`
      : 'RSI'

    // ── 검색 이력 DB 저장 ────────────────────────────────────
    await getDb().searchHistory.create({
      data: {
        clerkUserId: userId,
        ticker:      ticker.toUpperCase(),
        candle,
        strategy,
        rsiPeriod:   rsi_period,
        oversold,
        overbought,
        macdFast:    macd_fast,
        macdSlow:    macd_slow,
        macdSignal:  macd_signal,
        rsiLookback: rsi_lookback,
        capital,
      },
    }).catch(e => console.error('검색 이력 저장 실패:', e))

    return NextResponse.json({
      ticker:          ticker.toUpperCase(),
      candle_label:    meta.label,
      strategy_label:  strategyLabel,
      period_start:    fmtDate(data[0].date),
      period_end:      fmtDate(data[data.length - 1].date),
      initial_capital: capital,
      final_capital:   result.finalCapital,
      total_profit:    round(result.finalCapital - capital, 2),
      return_rate:     round((result.finalCapital - capital) / capital * 100, 4),
      total_trades:    stats.totalTrades,
      win_trades:      stats.winTrades,
      lose_trades:     stats.loseTrades,
      win_rate:        round(stats.winRate, 2),
      max_drawdown:    round(stats.maxDrawdown, 2),
      trades:          result.trades,
      chart_png:       '',
      chart_data:      chartData,
    })
  } catch (e: unknown) {
    console.error(e)
    return NextResponse.json({ detail: e instanceof Error ? e.message : '서버 오류' }, { status: 400 })
  }
}
