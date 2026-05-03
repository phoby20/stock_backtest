"use client"
import { useState } from "react"
import BacktestForm from "@/components/BacktestForm"
import BacktestResult from "@/components/BacktestResult"
import AuthButton from "@/components/AuthButton"
import { runBacktest, BacktestRequest, BacktestResponse } from "@/lib/api"

export default function HomePage() {
  const [result,  setResult]  = useState<BacktestResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error,   setError]   = useState<string | null>(null)

  const handleSubmit = async (req: BacktestRequest) => {
    setLoading(true)
    setError(null)
    setResult(null)
    try {
      const data = await runBacktest(req)
      setResult(data)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "알 수 없는 오류")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gh-base text-gh-text flex flex-col">
      {/* 헤더 */}
      <header className="border-b border-gh-border px-6 py-3 flex items-center gap-3 shrink-0">
        <span className="text-gh-blue text-lg">📈</span>
        <div>
          <h1 className="text-base font-semibold text-gh-text leading-none">Stock Backtest</h1>
          <p className="text-xs text-gh-muted mt-0.5">RSI + MACD 전략 자동매매 시뮬레이터</p>
        </div>
        <div className="ml-auto">
          <AuthButton />
        </div>
      </header>

      <div className="flex flex-1 overflow-hidden">
        {/* 사이드바 */}
        <aside className="w-72 shrink-0 border-r border-gh-border bg-gh-surface overflow-y-auto p-4">
          <BacktestForm onSubmit={handleSubmit} loading={loading} />
        </aside>

        {/* 메인 영역 */}
        <main className="flex-1 overflow-y-auto p-6">
          {error && (
            <div className="bg-gh-red/10 border border-gh-red/30 text-gh-red px-4 py-3 rounded-lg mb-5 text-sm">
              ⚠️ {error}
            </div>
          )}

          {loading && (
            <div className="flex flex-col items-center justify-center h-64 gap-3">
              <div className="w-8 h-8 border-2 border-gh-blue border-t-transparent rounded-full animate-spin" />
              <p className="text-gh-muted text-sm">데이터 수집 및 백테스트 실행 중…</p>
            </div>
          )}

          {result && !loading && <BacktestResult result={result} />}

          {!result && !loading && !error && (
            <div className="flex flex-col items-center justify-center h-64 gap-2 text-center">
              <p className="text-gh-muted text-sm">
                왼쪽 패널에서 파라미터를 설정하고<br />
                <span className="text-gh-blue">▶ 백테스트 실행</span>을 눌러 시작하세요.
              </p>
            </div>
          )}
        </main>
      </div>
    </div>
  )
}
