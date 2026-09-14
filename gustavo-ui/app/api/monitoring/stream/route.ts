import { NextRequest } from "next/server";

const FASTAPI_URL = process.env.FASTAPI_URL || "http://localhost:8000";

/**
 * Proxy the FastAPI SSE stream.
 * next.config.mjs rewrites buffer responses, which breaks SSE.
 * This route handler streams directly without buffering.
 */
export async function GET(request: NextRequest) {
  const { searchParams } = request.nextUrl;
  const device_group = searchParams.get("device_group") || "all";
  const host = searchParams.get("host") || "all";

  // EventSource can't set an Authorization header, so the browser sends the
  // gustavo_token cookie instead (mirrored there by AuthContext on login).
  // Forward it as a real Bearer header so the FastAPI /stream route can be
  // gated with the same verify_firebase_token dependency as every other
  // monitoring endpoint. No cookie at all is also valid, deliberately not
  // 401'd here: AUTH_ENABLED=false never sets one (the whole login flow is
  // skipped in that mode - see AuthContext.tsx), and verify_firebase_token
  // already ignores credentials entirely when AUTH_ENABLED is false. So the
  // upstream call is the single source of truth for whether this request is
  // allowed, not a local cookie-presence check here - matching how every
  // other endpoint in this app already defers to the backend rather than
  // gating on the frontend.
  const token = request.cookies.get("gustavo_token")?.value;
  const headers: Record<string, string> = { Accept: "text/event-stream" };
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const upstream = await fetch(
    `${FASTAPI_URL}/api/monitoring/stream?device_group=${encodeURIComponent(device_group)}&host=${encodeURIComponent(host)}`,
    { headers }
  );

  if (upstream.status === 401 || upstream.status === 403) {
    return new Response("Unauthorized", { status: upstream.status });
  }

  if (!upstream.body) {
    return new Response("No stream body from upstream", { status: 502 });
  }

  return new Response(upstream.body, {
    headers: {
      "Content-Type": "text/event-stream",
      "Cache-Control": "no-cache, no-transform",
      Connection: "keep-alive",
      "X-Accel-Buffering": "no",
    },
  });
}
