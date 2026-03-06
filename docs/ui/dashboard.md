# Dashboard

The Dashboard is the landing page after login. It provides an at-a-glance view of the platform state.

---

## Layout

```
┌─────────────────────────────────────────────────────┐
│  Platform Services                                   │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐       │
│  │ Redis  │ │ Mongo  │ │Registry│ │Manager │       │
│  │  Up ●  │ │  Up ●  │ │  Up ●  │ │  Up ●  │       │
│  └────────┘ └────────┘ └────────┘ └────────┘       │
│  ▶ Manage Platform Services                          │
├───────────────┬──────────────┬──────────────────────┤
│ System Vitals │     Apps     │   Device Groups       │
│ CPU  ████ 23% │              │                       │
│ Mem  ██   50% │      4       │         3             │
│ Disk ███  60% │ apps deployed│   groups configured   │
├───────────────┴──────────────┴──────────────────────┤
│  Recent Activity                                     │
│  Redis launched       Launching Redis…    2 min ago  │
│  Settings saved       Config updated      5 min ago  │
└─────────────────────────────────────────────────────┘
```

---

## Platform Services card

Always visible. Shows a status pill for each of the 4 platform services (Redis, MongoDB, Registry, Manager).

- **Green pulsing dot** — service is `Up`
- **Red dot** — service is `Down`
- **Gray** — status unknown (loading)

The status strip auto-refreshes every 30 seconds. Clicking **Status** in the expanded table forces an immediate refresh and updates the strip.

### Manage Platform Services (expandable)

Click the `▶ Manage Platform Services` toggle to expand a table with action buttons:

| Column | Actions |
|--------|---------|
| Primary | **Status**, **Launch**, **Restart** |
| Danger | **Stop**, **Remove** (with confirmation) |

**Launch** is a background operation — a spinner appears while the job is pending, then the status pill updates. **Stop** and **Remove** show a confirmation dialog before executing.

---

## System Vitals card

Shows live CPU, memory, and disk usage from worker nodes via the SSE monitoring stream. A drop-down lets you filter by device group and host.

Threshold colors:
- **Red** ≥ 80%
- **Yellow** ≥ 50%
- **Blue** < 50%

---

## Apps and Device Groups cards

Count of deployed apps and configured device groups. Click **Manage →** to navigate to the respective page.

---

## Recent Activity

The last 8 actions taken in the current session (launches, saves, errors). Sourced from the in-memory activity log (`lib/activityLog.ts`). Click the history icon in the sidebar footer to see the full log.

---

## Sidebar health dot

The Dashboard link in the sidebar shows a small dot:
- **Green** — all 4 services (Redis, MongoDB, Registry, Manager) are `Up`
- **Red** — at least one service is down
- **Gray** — status not yet loaded
