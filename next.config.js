/** @type {import('next').NextConfig} */
const nextConfig = {
  // base64 chart image는 next/image 최적화 불필요
  images: { unoptimized: true },
}

module.exports = nextConfig
