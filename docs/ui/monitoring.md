# Monitoring

Real-time platform metrics streamed from worker nodes via Server-Sent Events.

---

## Overview

The Monitoring page displays:
- **System Vitals** — CPU percentage over time (line chart), current memory and disk usage
- **Container Stats** — Per-container CPU and memory for each running app
- **Host selector** — Filter by device group and/or specific host

Data updates automatically every 10 seconds without page refresh.

---

## Connection status

A yellow banner appears when the SSE stream is disconnected:

```
⚠  Monitoring stream disconnected — data may be stale
```

The stream reconnects automatically when the browser re-establishes the connection.

---

## Threshold colors

| Usage | Color |
|-------|-------|
| ≥ 80% | Red |
| ≥ 50% | Yellow/amber |
| < 50% | Blue (normal) |

---

## Filtering

Use the drop-downs to filter by:
- **Device Group** — shows metrics only for workers in the selected group
- **Host** — shows metrics for a single worker node

Changing the filter re-connects the SSE stream with updated query parameters.

---

## Charts

**CPU over time** — line chart with a 5-minute rolling buffer (up to 300 data points at 10-second intervals). Powered by Recharts.

**Container breakdown** — bar or table showing per-container CPU % and memory usage for the currently selected host.

---

## How it works

```
Worker → Redis (pickled metrics, CACHE_EXPIRE_TIME TTL)
              ↓
FastAPI /api/monitoring/stream (SSE, 10s interval)
              ↓  build_cache() → Cache.getAssetsForAll()
              ↓  _extract_vitals() + _extract_containers()
              ↓  JSON payload over SSE
              ↓
Next.js useMonitoringStream hook
              ↓  EventSource listener
              ↓  5-min rolling VitalsPoint[] buffer
              ↓
MetricsChart (Recharts)
```
