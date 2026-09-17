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
  async headers() {
    return [
      {
        source: "/:path*",
        headers: [
          {
            // 'unsafe-inline' on script-src and style-src: most of
            // gustavo's pages are statically prerendered at build time
            // (no per-request context), which rules out a nonce-based
            // strict CSP - Next.js's own hydration scripts need a nonce
            // stamped in per-request, and a static page has no request to
            // stamp one from (verified: with a nonce-only script-src,
            // Next.js's own chunk scripts got blocked on every page,
            // confirmed via a live headless-browser console-error sweep).
            // The directive doing the actual protective work here is
            // connect-src 'self': even a script that's allowed to run
            // still can't fetch()/XHR data out to an attacker-controlled
            // origin, which is what actually matters if a stored-XSS
            // payload ever executes in an admin's browser.
            key: "Content-Security-Policy",
            value:
              "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self' data:; connect-src 'self'",
          },
          {
            // Blocks this app from being loaded inside an <iframe> on
            // another site (clickjacking) - nothing about gustavo needs
            // to be embeddable.
            key: "X-Frame-Options",
            value: "DENY",
          },
        ],
      },
    ];
  },
};

export default nextConfig;
