/** @type {import('next').NextConfig} */
const FASTAPI_URL = process.env.FASTAPI_URL || "http://127.0.0.1:8000";

const nextConfig = {
  output: "standalone",
  images: { unoptimized: true },
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${FASTAPI_URL}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
