"use client"
import { useState } from "react"
import BacktestForm from "@/components/BacktestForm"
import BacktestResult from "@/components/BacktestResult"
import AuthButton from "@/components/AuthButton"
import { runBacktest, BacktestRequest, BacktestResponse } from "@/lib/api"

export default function HomePage() {
  const [result,   setResult]   = useState<BacktestResponse | null>(null)
  const [loading,  setLoading]  = useState(false)
  const [error,    setError]    = useState<string | null>(null)
  const [formOpen, setFormOpen] = useState(true)

  const handleSubmit = async (req: BacktestRequest) => {
    setLoading(true)
    setError(null)
    setResult(null)
    setFormOpen(false) // 모바일: 실행 후 결과 화면으로 전환
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
    <div className="h-dvh bg-gh-base text-gh-text flex flex-col overflow-hidden">

      {/* ── 헤더 ── */}
      <header className="border-b border-gh-border px-4 lg:px-6 py-3 flex items-center gap-2 shrink-0">
        <span className="text-gh-blue text-lg">📈</span>
        <div className="min-w-0">
          <h1 className="text-sm lg:text-base font-semibold text-gh-text leading-none">Stock Backtest</h1>
          <p className="text-xs text-gh-muted mt-0.5 hidden sm:block">RSI + MACD 전략 자동매매 시뮬레이터</p>
        </div>

        {/* 모바일 전용 토글 */}
        <button
          onClick={() => setFormOpen(v => !v)}
          className="lg:hidden ml-2 shrink-0 text-xs border border-gh-border2 text-gh-muted px-2.5 py-1 rounded transition-colors hover:border-gh-blue hover:text-gh-blue"
        >
          {formOpen ? "📊 결과" : "⚙ 설정"}
        </button>

        <div className="ml-auto shrink-0">
          <AuthButton />
        </div>
      </header>

      {/* ── 바디 ── */}
      <div className="flex flex-1 overflow-hidden flex-col lg:flex-row">

        {/* 사이드바 (데스크톱) / 접힘 패널 (모바일) */}
        <aside className={[
          "bg-gh-surface border-gh-border overflow-y-auto",
          "lg:w-72 lg:border-r lg:shrink-0 lg:flex-none",
          formOpen ? "flex-1 border-b lg:border-b-0" : "hidden lg:block",
        ].join(" ")}>
          <div className="p-4">
            <BacktestForm onSubmit={handleSubmit} loading={loading} />
          </div>
        </aside>

        {/* 메인 결과 영역 */}
        <main className={[
          "flex-1 overflow-y-auto p-4 lg:p-6 w-full",
          formOpen ? "hidden lg:block" : "",
        ].join(" ")}>
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
                <span className="lg:hidden">
                  상단 <span className="text-gh-blue">⚙ 설정</span>에서 파라미터를 입력하고<br />
                </span>
                <span className="hidden lg:inline">
                  왼쪽 패널에서 파라미터를 설정하고<br />
                </span>
                <span className="text-gh-blue">▶ 백테스트 실행</span>을 눌러 시작하세요.
              </p>
            </div>
          )}
        </main>
      </div>
    </div>
  )
}
