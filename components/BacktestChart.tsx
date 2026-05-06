"use client"
import { useState, useEffect } from 'react'
import {
  ComposedChart, Line, Area, Bar, Cell, ReferenceLine,
  XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid,
} from 'recharts'
import type { ChartPoint } from '@/lib/api'

interface Props {
  data:           ChartPoint[]
  initialCapital: number
  ticker:         string
  candleLabel:    string
  strategyLabel:  string
  returnRate:     number
  periodStart:    string
  periodEnd:      string
}

const BG     = '#161b22'
const GRID   = { strokeDasharray: '3 3', stroke: '#30363d' }
const TICK   = { fontSize: 10, fill: '#8b949e', fontFamily: "'Noto Sans KR', 'Apple SD Gothic Neo', sans-serif" }
const TIP    = { background: BG, border: '1px solid #30363d', fontSize: 11, color: '#c9d1d9', fontFamily: "'Noto Sans KR', 'Apple SD Gothic Neo', sans-serif" }
const MARGIN = { left: 0, right: 8, top: 4, bottom: 0 }

function useMobile() {
  const [mobile, setMobile] = useState(false)
  useEffect(() => {
    const mq = window.matchMedia('(max-width: 639px)')
    setMobile(mq.matches)
    const handler = (e: MediaQueryListEvent) => setMobile(e.matches)
    mq.addEventListener('change', handler)
    return () => mq.removeEventListener('change', handler)
  }, [])
  return mobile
}

/* eslint-disable @typescript-eslint/no-explicit-any */
const fmtPrice = (v: any) => typeof v === 'number' ? [v.toLocaleString('ko-KR', { maximumFractionDigits: 2 }), '종가'] as const : ['', '종가'] as const
const fmtRsi   = (v: any) => typeof v === 'number' ? [v.toFixed(2), 'RSI'] as const : ['', 'RSI'] as const
const fmtMacd  = (v: any) => typeof v === 'number' ? [v.toFixed(4), ''] as const : ['', ''] as const
const fmtAsset = (v: any) => typeof v === 'number' ? [v.toLocaleString('ko-KR'), '자산'] as const : ['', '자산'] as const
/* eslint-enable @typescript-eslint/no-explicit-any */

export default function BacktestChart({
  data, initialCapital, ticker, candleLabel, strategyLabel, returnRate, periodStart, periodEnd,
}: Props) {
  const mobile = useMobile()
  const yW = mobile ? 52 : 66
  const h1 = mobile ? 160 : 200
  const h2 = mobile ? 80  : 100
  const h3 = mobile ? 80  : 100
  const h4 = mobile ? 88  : 110

  const isProfit   = returnRate >= 0
  const rateColor  = isProfit ? '#3fb950' : '#f85149'
  const capitalFmt = initialCapital.toLocaleString('ko-KR')

  return (
    <div style={{ background: BG }}>
      {/* 차트 타이틀 */}
      <div className="px-1 py-1.5 text-center" style={{ background: BG }}>
        <p className="text-xs text-gh-muted leading-snug">
          <span className="font-semibold text-gh-text">{ticker}</span>
          {' '}
          <span>[{candleLabel} / {strategyLabel}]</span>
          {' '}
          <span style={{ color: rateColor }}>수익률: {isProfit ? '+' : ''}{returnRate.toFixed(2)}%</span>
          {' | '}
          <span>{periodStart} ~ {periodEnd}</span>
        </p>
      </div>

      <div className="space-y-1">
        {/* Panel 1: Price + buy/sell dots */}
        <div className="relative" style={{ background: BG }}>
          {/* 범례 */}
          <div className="absolute top-1 right-2 z-10 flex gap-2 select-none" style={{ fontSize: 9 }}>
            <span style={{ color: '#4C9BE8' }}>— 종가</span>
            <span style={{ color: '#00C853' }}>▲ 매수</span>
            <span style={{ color: '#FF3D00' }}>▽ 매도</span>
          </div>
          <span className="absolute top-1 left-1 z-10 text-[9px] text-gh-muted uppercase tracking-wide select-none">종가</span>
          <ResponsiveContainer width="100%" height={h1}>
            <ComposedChart data={data} margin={MARGIN} style={{ background: BG }}>
              <CartesianGrid {...GRID} />
              <XAxis dataKey="date" hide />
              <YAxis tick={TICK} tickLine={false} width={yW} tickFormatter={(v) => v.toLocaleString()} />
              <Tooltip contentStyle={TIP} formatter={fmtPrice} />
              <Area
                type="monotone"
                dataKey="close"
                stroke="#4C9BE8"
                strokeWidth={1.5}
                fill="#4C9BE8"
                fillOpacity={0.1}
                name="종가"
                dot={(props: Record<string, unknown>) => {
                  const { payload, cx, cy } = props as { payload: ChartPoint; cx: number; cy: number }
                  if (payload.signal === 'BUY')  return <polygon key={`b${cx}`} points={`${cx},${cy - 7} ${cx - 5},${cy + 2} ${cx + 5},${cy + 2}`} fill="#00C853" />
                  if (payload.signal === 'SELL') return <polygon key={`s${cx}`} points={`${cx},${cy + 7} ${cx - 5},${cy - 2} ${cx + 5},${cy - 2}`} fill="#FF3D00" />
                  return <circle key={`n${cx}`} cx={0} cy={0} r={0} fill="none" />
                }}
                activeDot={{ r: 4 }}
              />
            </ComposedChart>
          </ResponsiveContainer>
        </div>

        {/* Panel 2: RSI */}
        <div className="relative" style={{ background: BG }}>
          <span className="absolute top-1 left-1 z-10 text-[9px] text-gh-muted uppercase tracking-wide select-none">RSI</span>
          <ResponsiveContainer width="100%" height={h2}>
            <ComposedChart data={data} margin={MARGIN} style={{ background: BG }}>
              <CartesianGrid {...GRID} />
              <XAxis dataKey="date" hide />
              <YAxis tick={TICK} tickLine={false} width={yW} domain={[0, 100]} ticks={[0, 30, 70, 100]} />
              <Tooltip contentStyle={TIP} formatter={fmtRsi} />
              <ReferenceLine y={70} stroke="#FF3D00" strokeDasharray="4 2" strokeOpacity={0.8}
                label={{ value: '매도(70)', position: 'right', fill: '#FF3D00', fontSize: 9 }} />
              <ReferenceLine y={30} stroke="#00C853" strokeDasharray="4 2" strokeOpacity={0.8}
                label={{ value: '매수(30)', position: 'right', fill: '#00C853', fontSize: 9 }} />
              <Line type="monotone" dataKey="rsi" stroke="#AB47BC" dot={false} strokeWidth={1.2} connectNulls name="RSI" />
            </ComposedChart>
          </ResponsiveContainer>
        </div>

        {/* Panel 3: MACD */}
        <div className="relative" style={{ background: BG }}>
          <span className="absolute top-1 left-1 z-10 text-[9px] text-gh-muted uppercase tracking-wide select-none">MACD</span>
          {/* MACD 범례 */}
          <div className="absolute top-1 right-2 z-10 flex gap-2 select-none" style={{ fontSize: 9 }}>
            <span style={{ color: '#4C9BE8' }}>— MACD</span>
            <span style={{ color: '#F57F17' }}>— Signal</span>
          </div>
          <ResponsiveContainer width="100%" height={h3}>
            <ComposedChart data={data} margin={MARGIN} style={{ background: BG }}>
              <CartesianGrid {...GRID} />
              <XAxis dataKey="date" hide />
              <YAxis tick={TICK} tickLine={false} width={yW} tickFormatter={(v) => v.toFixed(2)} />
              <Tooltip contentStyle={TIP} formatter={fmtMacd} />
              <ReferenceLine y={0} stroke="#8b949e" strokeOpacity={0.5} />
              <Bar dataKey="macdHist" maxBarSize={4} name="Hist">
                {data.map((entry, i) => (
                  <Cell key={i} fill={entry.macdHist >= 0 ? '#00C853' : '#FF3D00'} fillOpacity={0.5} />
                ))}
              </Bar>
              <Line type="monotone" dataKey="macd"       stroke="#4C9BE8" dot={false} strokeWidth={1.2} name="MACD" />
              <Line type="monotone" dataKey="macdSignal" stroke="#F57F17" dot={false} strokeWidth={1.2} name="Signal" />
            </ComposedChart>
          </ResponsiveContainer>
        </div>

        {/* Panel 4: Portfolio */}
        <div className="relative" style={{ background: BG }}>
          <span className="absolute top-1 left-1 z-10 text-[9px] text-gh-muted uppercase tracking-wide select-none">자산</span>
          <ResponsiveContainer width="100%" height={h4}>
            <ComposedChart data={data} margin={{ ...MARGIN, bottom: 5 }} style={{ background: BG }}>
              <CartesianGrid {...GRID} />
              <XAxis dataKey="date" tick={TICK} tickLine={false} interval="preserveStartEnd" />
              <YAxis tick={TICK} tickLine={false} width={yW} tickFormatter={(v: number) => {
                const abs = Math.abs(v)
                if (abs >= 1_000_000) return (v / 1_000_000).toFixed(1) + 'M'
                if (abs >= 1_000)     return (v / 1_000).toFixed(1) + 'K'
                return v.toFixed(0)
              }} />
              <Tooltip contentStyle={TIP} formatter={fmtAsset} />
              <ReferenceLine y={initialCapital} stroke="#8b949e" strokeDasharray="4 2" strokeOpacity={0.7}
                label={{ value: `초기자본 ${capitalFmt}`, position: 'insideTopRight', fill: '#8b949e', fontSize: 9 }} />
              <Area type="monotone" dataKey="portfolio" stroke="#00C853" fill="#00C853" fillOpacity={0.1} dot={false} strokeWidth={1.2} name="자산" />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  )
}
