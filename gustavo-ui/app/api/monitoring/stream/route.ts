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

  const upstream = await fetch(
    `${FASTAPI_URL}/api/monitoring/stream?device_group=${encodeURIComponent(device_group)}&host=${encodeURIComponent(host)}`,
    { headers: { Accept: "text/event-stream" } }
  );

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
