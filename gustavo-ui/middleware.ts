import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

// Check runtime AUTH_ENABLED first (Edge Runtime compatible, no NEXT_PUBLIC_ prefix needed).
// Falls back to the build-time baked value so local `npm run dev` still works.
// Use only the runtime env var — NEXT_PUBLIC_AUTH_ENABLED is baked at build
// time and cannot be toggled without a rebuild, so we ignore it here.
const AUTH_ENABLED = process.env.AUTH_ENABLED === "true";
const PUBLIC_PATHS = ["/login", "/api/auth"];

export function middleware(request: NextRequest) {
  if (!AUTH_ENABLED) return NextResponse.next();

  const { pathname } = request.nextUrl;

  // Allow public paths
  if (PUBLIC_PATHS.some((p) => pathname.startsWith(p))) {
    return NextResponse.next();
  }

  // Check for token in cookie (set by /login page after successful auth)
  const token = request.cookies.get("gustavo_token")?.value;
  if (!token) {
    const loginUrl = new URL("/login", request.url);
    loginUrl.searchParams.set("redirect", pathname);
    return NextResponse.redirect(loginUrl);
  }

  return NextResponse.next();
}

export const config = {
  // Exclude: Next.js internals, API routes, and any path with a file extension
  // (static assets like .png, .svg, .js, .css, etc. — served directly, no auth needed).
  matcher: ["/((?!_next/static|_next/image|favicon.ico|api/|.*\\.\\w{1,4}$).*)"],
};
