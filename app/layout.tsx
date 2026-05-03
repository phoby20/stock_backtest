import type { Metadata } from "next"
import "./globals.css"
import AuthProvider from "@/components/AuthProvider"

export const metadata: Metadata = {
  title: "Stock Backtest",
  description: "RSI + MACD 전략 백테스트 웹앱",
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ko">
      <body>
        <AuthProvider>{children}</AuthProvider>
      </body>
    </html>
  )
}
