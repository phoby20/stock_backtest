import { NextResponse } from 'next/server'

export async function GET() {
  return NextResponse.json({
    '1m':  { label: '1분봉',   max_period: '7d',   auto_lookback: 10 },
    '5m':  { label: '5분봉',   max_period: '60d',  auto_lookback: 10 },
    '15m': { label: '15분봉',  max_period: '60d',  auto_lookback: 10 },
    '30m': { label: '30분봉',  max_period: '60d',  auto_lookback: 10 },
    '1h':  { label: '1시간봉', max_period: '730d', auto_lookback: 12 },
    '1d':  { label: '일봉',    max_period: '5y',   auto_lookback: 20 },
  })
}
