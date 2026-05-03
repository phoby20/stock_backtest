'use client'
import { useSession, signIn, signOut } from 'next-auth/react'
import Image from 'next/image'

export default function AuthButton() {
  const { data: session, status } = useSession()

  if (status === 'loading') {
    return <div className="w-20 h-7 bg-gh-border rounded animate-pulse" />
  }

  if (session?.user) {
    return (
      <div className="flex items-center gap-2">
        {session.user.image && (
          <Image
            src={session.user.image}
            alt={session.user.name ?? ''}
            width={24}
            height={24}
            className="rounded-full"
          />
        )}
        <span className="text-xs text-gh-muted hidden sm:block">{session.user.name}</span>
        <button
          onClick={() => signOut()}
          className="text-xs text-gh-muted hover:text-gh-text border border-gh-border px-2 py-1 rounded transition-colors"
        >
          로그아웃
        </button>
      </div>
    )
  }

  return (
    <button
      onClick={() => signIn('google')}
      className="text-xs bg-gh-blue hover:opacity-90 text-white font-medium px-3 py-1.5 rounded transition-opacity"
    >
      Google로 로그인
    </button>
  )
}
