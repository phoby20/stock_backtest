import { PrismaClient } from '@prisma/client'
import { withAccelerate } from '@prisma/extension-accelerate'

const createClient = () => new PrismaClient().$extends(withAccelerate())

type PrismaClientWithAccelerate = ReturnType<typeof createClient>
const globalForPrisma = globalThis as unknown as { prisma: PrismaClientWithAccelerate }

export const prisma = globalForPrisma.prisma ?? createClient()

if (process.env.NODE_ENV !== 'production') globalForPrisma.prisma = prisma

export default prisma
