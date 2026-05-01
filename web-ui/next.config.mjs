/** @type {import('next').NextConfig} */
const nextConfig = {
  env: {
    N8N_WEBHOOK_URL: process.env.N8N_WEBHOOK_URL,
  },
}

export default nextConfig
