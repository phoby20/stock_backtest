"use client"
import { useState, useEffect } from "react"
import { useUser, SignInButton } from "@clerk/nextjs"
import { BacktestRequest } from "@/lib/api"

const CANDLE_OPTIONS = [
  { value: "1d",  label: "일봉 (최대 5년)",     autoLookback: 20 },
  { value: "1h",  label: "1시간봉 (최대 730일)", autoLookback: 12 },
  { value: "30m", label: "30분봉 (최대 60일)",   autoLookback: 10 },
  { value: "15m", label: "15분봉 (최대 60일)",   autoLookback: 10 },
  { value: "5m",  label: "5분봉 (최대 60일)",    autoLookback: 10 },
  { value: "1m",  label: "1분봉 (최대 7일)",     autoLookback: 10 },
]

const INPUT_CLS =
  "w-full bg-gh-base border border-gh-border2 text-gh-text rounded px-3 py-2 text-sm " +
  "focus:outline-none focus:border-gh-blue transition-colors"

const LABEL_CLS = "block text-xs font-semibold text-gh-muted uppercase tracking-wide mb-1"

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <label className={LABEL_CLS}>{label}</label>
      {children}
    </div>
  )
}

function SectionTitle({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex items-center gap-2 pt-1">
      <span className="text-xs font-semibold text-gh-muted uppercase tracking-wide">{children}</span>
      <div className="flex-1 h-px bg-gh-border" />
    </div>
  )
}

interface Props {
  onSubmit: (req: BacktestRequest) => void
  loading:  boolean
}

export default function BacktestForm({ onSubmit, loading }: Props) {
  const { isSignedIn } = useUser()
  const isLoggedIn = !!isSignedIn

  const [ticker,     setTicker]     = useState("AAPL")
  const [candle,     setCandle]     = useState("1d")
  const [capital,    setCapital]    = useState(10_000_000)
  const [strategy,   setStrategy]   = useState("rsi-macd")
  const [rsiPeriod,  setRsiPeriod]  = useState(14)
  const [oversold,   setOversold]   = useState(30)
  const [overbought, setOverbought] = useState(70)
  const [macdFast,   setMacdFast]   = useState(12)
  const [macdSlow,   setMacdSlow]   = useState(26)
  const [macdSig,    setMacdSig]    = useState(9)
  const [lookback,   setLookback]   = useState(20)

  // 봉 단위 변경 시 lookback 자동 갱신
  useEffect(() => {
    const opt = CANDLE_OPTIONS.find(o => o.value === candle)
    if (opt) setLookback(opt.autoLookback)
  }, [candle])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onSubmit({
      ticker:       ticker.trim().toUpperCase(),
      candle,
      capital,
      strategy,
      rsi_period:   rsiPeriod,
      oversold,
      overbought,
      macd_fast:    macdFast,
      macd_slow:    macdSlow,
      macd_signal:  macdSig,
      rsi_lookback: lookback,
    })
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <SectionTitle>종목 · 기본</SectionTitle>

      <Field label="종목코드">
        <input
          type="text" value={ticker} onChange={e => setTicker(e.target.value)}
          className={INPUT_CLS} placeholder="예: AAPL, SOXL, 005930.KS" required
        />
      </Field>

      <Field label="봉 단위">
        <select value={candle} onChange={e => setCandle(e.target.value)} className={INPUT_CLS}>
          {CANDLE_OPTIONS.map(o => (
            <option key={o.value} value={o.value}>{o.label}</option>
          ))}
        </select>
      </Field>

      <Field label="초기자본">
        <input
          type="number" value={capital} onChange={e => setCapital(Number(e.target.value))}
          className={INPUT_CLS} min={1000} step={100000}
        />
      </Field>

      <Field label="전략">
        <select value={strategy} onChange={e => setStrategy(e.target.value)} className={INPUT_CLS}>
          <option value="rsi-macd">RSI + MACD (복합)</option>
          <option value="rsi">RSI 단독</option>
        </select>
      </Field>

      <SectionTitle>RSI 파라미터</SectionTitle>

      <div className="grid grid-cols-3 gap-2">
        {[
          { label: "기간",   val: rsiPeriod,  set: setRsiPeriod,  min: 2,  max: 50 },
          { label: "매수 ≤", val: oversold,   set: setOversold,   min: 1,  max: 49 },
          { label: "매도 ≥", val: overbought, set: setOverbought, min: 51, max: 99 },
        ].map(({ label, val, set, min, max }) => (
          <div key={label}>
            <label className="block text-xs text-gh-muted mb-1">{label}</label>
            <input type="number" value={val} onChange={e => set(Number(e.target.value))}
              min={min} max={max}
              className="w-full bg-gh-base border border-gh-border2 text-gh-text rounded px-2 py-1.5 text-sm focus:outline-none focus:border-gh-blue"
            />
          </div>
        ))}
      </div>

      {strategy === "rsi-macd" && (
        <>
          <SectionTitle>MACD 파라미터</SectionTitle>

          <div className="grid grid-cols-3 gap-2">
            {[
              { label: "단기",   val: macdFast, set: setMacdFast, min: 2, max: 100 },
              { label: "장기",   val: macdSlow, set: setMacdSlow, min: 2, max: 200 },
              { label: "시그널", val: macdSig,  set: setMacdSig,  min: 2, max: 50  },
            ].map(({ label, val, set, min, max }) => (
              <div key={label}>
                <label className="block text-xs text-gh-muted mb-1">{label}</label>
                <input type="number" value={val} onChange={e => set(Number(e.target.value))}
                  min={min} max={max}
                  className="w-full bg-gh-base border border-gh-border2 text-gh-text rounded px-2 py-1.5 text-sm focus:outline-none focus:border-gh-blue"
                />
              </div>
            ))}
          </div>

          <Field label={`RSI Lookback — ${lookback}봉`}>
            <input
              type="range" value={lookback} onChange={e => setLookback(Number(e.target.value))}
              min={1} max={50} className="w-full mt-1"
            />
            <p className="text-xs text-gh-dim mt-1">
              RSI 조건 충족 후 MACD 크로스 대기 기간
            </p>
          </Field>
        </>
      )}

      {isLoggedIn ? (
        <button
          type="submit" disabled={loading}
          className="w-full bg-gh-merge hover:bg-gh-mergeHover disabled:bg-gh-border disabled:cursor-not-allowed
                     text-white font-semibold py-2.5 rounded text-sm transition-colors mt-2"
        >
          {loading ? "실행 중…" : "▶  백테스트 실행"}
        </button>
      ) : (
        <SignInButton mode="modal">
          <button
            type="button"
            className="w-full bg-gh-blue hover:opacity-90 text-white font-semibold py-2.5 rounded text-sm transition-opacity mt-2"
          >
            로그인 후 실행
          </button>
        </SignInButton>
      )}
    </form>
  )
}
