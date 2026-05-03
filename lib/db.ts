import { PrismaClient } from '@prisma/client'
import { withAccelerate } from '@prisma/extension-accelerate'

type ExtendedClient = ReturnType<typeof createPrismaClient>
const g = globalThis as unknown as { prisma?: ExtendedClient }

function createPrismaClient() {
  return new PrismaClient().$extends(withAccelerate())
}

// 빌드 시가 아닌 첫 요청 때만 초기화 (lazy initialization)
export function getDb(): ExtendedClient {
  if (!g.prisma) g.prisma = createPrismaClient()
  return g.prisma
}
