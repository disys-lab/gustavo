# Component Reference

Key reusable components in `gustavo-ui/components/`.

---

## Layout

### `Sidebar`

`components/layout/Sidebar.tsx`

The persistent left sidebar present on all dashboard pages.

**Props:** none (uses hooks internally)

**Features:**
- Logo image (`/gustavo_wordmark.png`)
- Navigation links with active-link highlighting
- Service health dot on the Dashboard link (green/red/gray via `useServiceHealth`)
- Activity log sheet button
- Sign out button

---

### `ActivitySheet`

`components/layout/ActivitySheet.tsx`

A slide-in sheet (drawer) showing the full in-session activity log.

Triggered by the clock icon in the sidebar footer. Shows timestamped entries with color-coded level (success/error/info).

---

## Manager

### `ServiceRow`

`components/manager/ServiceRow.tsx`

A table row for a single platform service in the expandable "Manage Platform Services" table.

**Props:**

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `name` | `ServiceName` | required | Service identifier (`redis`, `mongo`, etc.) |
| `initialStatus` | `string` | `"Unknown"` | Initial status pill value |
| `showStatus` | `boolean` | `true` | Whether to render a status column |

**Features:**
- Status pill (Up / Down / Unknown)
- **Status** button — calls `GET /api/services/{svc}/status`, updates local status, invalidates the `["services"]` React Query cache so the dashboard strip refreshes
- **Launch** button — calls `POST /api/services/{svc}/run`, polls via `useJobPoller`
- **Restart** button — calls action `restart`
- **Stop** / **Remove** buttons — require confirmation via `AlertDialog`

---

## Apps

### `AppForm`

`components/apps/AppForm.tsx`

Full create/edit form for a Nebula application. Used on both `/apps` (create) and `/apps/[name]` (edit).

**Props:**

| Prop | Type | Description |
|------|------|-------------|
| `mode` | `"create" \| "edit"` | Controls which API call is made on submit |
| `initialValues` | `AppFormValues \| undefined` | Pre-populate form fields in edit mode |
| `appName` | `string \| undefined` | App name (disabled in edit mode) |
| `onSuccess` | `() => void` | Called after a successful save |

**Form schema (Zod):**

```typescript
{
  name: z.string().regex(/^[a-z0-9_-]+$/),
  docker_image: z.string().min(1),
  env_vars: z.array(z.object({ key: z.string(), value: z.string() })),
  ports: z.array(z.object({ host: z.number(), container: z.number() })),
  volumes: z.array(z.object({ host: z.string(), container: z.string() })),
  network_mode: z.string().optional(),
  running: z.boolean(),
  privileged: z.boolean(),
  device_groups: z.array(z.string()),
}
```

---

### `AppExpander`

`components/apps/AppExpander.tsx`

Expandable card showing an app's summary. Click the `ChevronDown`/`ChevronUp` icon to expand details.

---

### `YamlUpload`

`components/apps/YamlUpload.tsx`

File input that accepts `.yaml`/`.yml` files, posts to `/api/apps/yaml/parse`, and returns the parsed config dict to a callback.

---

## Monitoring

### `MetricsChart`

`components/monitoring/MetricsChart.tsx`

Recharts `LineChart` rendering CPU percentage over time from `VitalsPoint[]` buffer.

**Props:**

| Prop | Type | Description |
|------|------|-------------|
| `data` | `VitalsPoint[]` | Rolling buffer of `{timestamp, cpu_percent}` points |
| `height` | `number` | Chart height in pixels |

---

### `HostSelector`

`components/monitoring/HostSelector.tsx`

Drop-down selectors for device group and host filtering on the Monitoring page.

---

## Backups

### `BackupTable`

`components/backups/BackupTable.tsx`

Table listing backup files with timestamp, size, and action buttons (Restore, Delete). Single-row selection for restore operations.

**Props:**

| Prop | Type | Description |
|------|------|-------------|
| `type` | `"redis" \| "registry"` | Which backup endpoint to use |

Uses `date-fns` `formatDistanceToNow` for relative timestamps. Raw UTC timestamp shown in the `title` attribute on hover.

---

## Device Groups

### `DeviceGroupForm`

`components/device-groups/DeviceGroupForm.tsx`

Create/edit form for device groups with app multi-select.

---

### `AppSelector`

`components/device-groups/AppSelector.tsx`

Multi-select component for choosing apps from the deployed app list.

---

## UI Primitives

All from `components/ui/` — built on [shadcn/ui](https://ui.shadcn.com/).

| Component | Description |
|-----------|-------------|
| `StatusPill` | Badge showing Up (green pulsing dot) / Down (red) / Unknown (gray) |
| `TaskButton` | Button with loading spinner state |
| `Button` | Standard button with variants (default, outline, secondary, destructive) |
| `Card` | Content card with `CardHeader`, `CardContent`, `CardTitle` |
| `Dialog` / `AlertDialog` | Modal dialogs with confirm/cancel |
| `Accordion` | Expandable sections (used in Settings) |
| `Sheet` | Slide-in drawer (used in ActivitySheet) |
| `Tabs` | Tab navigation (used in Backups) |
| `Input` / `Label` | Form controls |
| `Badge` | Small status labels |
| `Skeleton` | Loading placeholder |
| `Toast` / `Toaster` | Notification toasts |

---

## Hooks

### `useServiceHealth`

`lib/hooks/useServiceHealth.ts`

Polls `GET /api/services` every 30 seconds. Returns `{ allUp: boolean | null }` based on whether all 4 platform services (redis, mongo, registry, manager) are up. Used by the Sidebar health dot.

---

### `useMonitoringStream`

`lib/hooks/useMonitoringStream.ts`

Opens an `EventSource` to `/api/monitoring/stream`. Maintains a 5-minute rolling buffer of `VitalsPoint[]` entries. Returns `{ buffer, lastEvent, connected, error }`.

---

### `useJobPoller`

`lib/hooks/useJobPoller.ts`

Polls `GET /api/services/jobs/{jobId}` every 1.5 seconds until `status` is `done` or `error`. Used by `ServiceRow` for Launch operations and `BackupTable` for create/restore operations.

Returns `{ isRunning, isDone, isError, job }`.
