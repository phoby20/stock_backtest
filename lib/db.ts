import { PrismaClient } from '@prisma/client'

const g = globalThis as unknown as { prisma?: PrismaClient }

export function getDb(): PrismaClient {
  if (!g.prisma) g.prisma = new PrismaClient()
  return g.prisma
}
