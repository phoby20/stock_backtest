'use client'
import { SignInButton, UserButton, useUser } from '@clerk/nextjs'

export default function AuthButton() {
  const { isSignedIn, user, isLoaded } = useUser()

  if (!isLoaded) {
    return <div className="w-20 h-7 bg-gh-border rounded animate-pulse" />
  }

  if (isSignedIn) {
    return (
      <div className="flex items-center gap-2">
        <span className="text-xs text-gh-muted hidden sm:block">{user.fullName}</span>
        <UserButton />
      </div>
    )
  }

  return (
    <SignInButton mode="modal">
      <button className="text-xs bg-gh-blue hover:opacity-90 text-white font-medium px-3 py-1.5 rounded transition-opacity">
        로그인
      </button>
    </SignInButton>
  )
}
