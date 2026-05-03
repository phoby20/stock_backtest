"use client"
import dynamic from "next/dynamic"
import { BacktestResponse, Trade } from "@/lib/api"

const BacktestChart = dynamic(() => import("@/components/BacktestChart"), { ssr: false })

interface Props { result: BacktestResponse }

function StatCard({
  label, value, sub, positive,
}: { label: string; value: string; sub?: string; positive?: boolean | null }) {
  const color =
    positive === true  ? "text-gh-green" :
    positive === false ? "text-gh-red"   : "text-gh-text"
  return (
    <div className="bg-gh-surface border border-gh-border rounded-lg p-3 sm:p-4">
      <p className="text-xs text-gh-muted mb-1">{label}</p>
      <p className={`text-lg sm:text-xl font-bold ${color} truncate`}>{value}</p>
      {sub && <p className="text-xs text-gh-muted mt-1 truncate">{sub}</p>}
    </div>
  )
}

function ActionBadge({ action }: { action: string }) {
  const isBuy = action.startsWith("BUY")
  return (
    <span className={`px-2 py-0.5 rounded text-xs font-medium whitespace-nowrap ${
      isBuy ? "bg-gh-green/20 text-gh-green" : "bg-gh-red/20 text-gh-red"
    }`}>
      {action}
    </span>
  )
}

const fmt = (n: number) =>
  n.toLocaleString("ko-KR", { maximumFractionDigits: 2 })

export default function BacktestResult({ result }: Props) {
  const isProfit = result.total_profit >= 0

  return (
    <div className="space-y-4 sm:space-y-6">

      {/* 헤더 */}
      <div className="border-b border-gh-border pb-3 sm:pb-4">
        <h2 className="text-base sm:text-lg font-semibold text-gh-text flex flex-wrap items-baseline gap-x-2 gap-y-1">
          {result.ticker}
          <span className="text-gh-muted font-normal text-xs sm:text-sm">
            {result.candle_label} / {result.strategy_label}
          </span>
        </h2>
        <p className="text-xs text-gh-muted mt-1">
          {result.period_start} ~ {result.period_end}
        </p>
      </div>

      {/* 지표 카드 */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-2 sm:gap-3">
        <StatCard
          label="총 수익"
          value={`${isProfit ? "+" : ""}${fmt(result.total_profit)}`}
          sub={`최종 ${fmt(result.final_capital)}`}
          positive={isProfit}
        />
        <StatCard
          label="수익률"
          value={`${isProfit ? "+" : ""}${result.return_rate.toFixed(2)}%`}
          positive={isProfit}
        />
        <StatCard
          label="거래 횟수"
          value={`${result.total_trades}회`}
          sub={`승 ${result.win_trades} / 패 ${result.lose_trades}`}
        />
        <StatCard
          label="승률"
          value={`${result.win_rate.toFixed(1)}%`}
          positive={result.win_rate >= 50}
        />
        <StatCard
          label="최대 낙폭"
          value={`-${result.max_drawdown.toFixed(2)}%`}
          positive={false}
        />
      </div>

      {/* 차트 */}
      {result.chart_data && result.chart_data.length > 0 && (
        <div className="bg-gh-surface border border-gh-border rounded-lg p-3 sm:p-4">
          <p className="text-xs font-semibold text-gh-muted uppercase tracking-wide mb-3">
            백테스트 차트
          </p>
          <BacktestChart data={result.chart_data} initialCapital={result.initial_capital} />
        </div>
      )}
      {result.chart_png && !result.chart_data && (
        <div className="bg-gh-surface border border-gh-border rounded-lg p-3 sm:p-4">
          <p className="text-xs font-semibold text-gh-muted uppercase tracking-wide mb-3">
            백테스트 차트
          </p>
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src={`data:image/png;base64,${result.chart_png}`} alt="backtest chart" className="w-full rounded" />
        </div>
      )}

      {/* 거래 내역 */}
      {result.trades.length > 0 && (
        <div className="bg-gh-surface border border-gh-border rounded-lg p-3 sm:p-4">
          <p className="text-xs font-semibold text-gh-muted uppercase tracking-wide mb-3">
            거래 내역 ({result.trades.length}건)
          </p>
          <div className="overflow-x-auto -mx-1">
            <table className="w-full text-xs sm:text-sm min-w-[420px]">
              <thead>
                <tr className="border-b border-gh-border text-gh-muted text-xs">
                  <th className="text-left py-2 pr-3 font-medium">날짜</th>
                  <th className="text-left py-2 pr-3 font-medium">구분</th>
                  <th className="text-right py-2 pr-3 font-medium">가격</th>
                  <th className="text-right py-2 pr-3 font-medium">금액</th>
                  <th className="text-right py-2 font-medium">RSI</th>
                </tr>
              </thead>
              <tbody>
                {result.trades.map((t: Trade, i: number) => (
                  <tr key={i} className="border-b border-gh-border/40 hover:bg-gh-base/50">
                    <td className="py-1.5 pr-3 text-gh-muted whitespace-nowrap">{t.date}</td>
                    <td className="py-1.5 pr-3"><ActionBadge action={t.action} /></td>
                    <td className="py-1.5 pr-3 text-right whitespace-nowrap">{fmt(t.price)}</td>
                    <td className="py-1.5 pr-3 text-right whitespace-nowrap">{fmt(t.amount)}</td>
                    <td className="py-1.5 text-right text-gh-muted">{t.rsi.toFixed(1)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
