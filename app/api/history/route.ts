import { NextRequest, NextResponse } from "next/server";
import { auth } from "@clerk/nextjs/server";
import { getDb } from "@/lib/db";

export async function POST(req: NextRequest) {
  const { userId } = await auth();
  if (!userId) return NextResponse.json({ ok: false }, { status: 401 });

  const {
    ticker,
    candle,
    capital,
    strategy,
    rsi_period,
    oversold,
    overbought,
    macd_fast,
    macd_slow,
    macd_signal,
    rsi_lookback,
  } = await req.json();

  const jstNow = new Date(Date.now() + 9 * 60 * 60 * 1000);

  try {
    await getDb().searchHistory.create({
      data: {
        clerkUserId: userId,
        ticker: String(ticker).toUpperCase(),
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
        createdAt:   jstNow,
      },
    });
    return NextResponse.json({ ok: true });
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : String(e);
    console.error("[이력 저장 실패]", msg);
    return NextResponse.json({ ok: false, error: msg }, { status: 500 });
  }
}
