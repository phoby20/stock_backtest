import type { Metadata } from "next"
import { Noto_Sans_KR } from "next/font/google"
import "./globals.css"
import { ClerkProvider } from "@clerk/nextjs"

const notoSansKR = Noto_Sans_KR({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-noto-sans-kr",
  display: "swap",
})

export const metadata: Metadata = {
  title: "Stock Backtest",
  description: "RSI + MACD 전략 백테스트 웹앱",
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <ClerkProvider>
      <html lang="ko" className={notoSansKR.variable}>
        <body className={notoSansKR.className}>{children}</body>
      </html>
    </ClerkProvider>
  )
}
