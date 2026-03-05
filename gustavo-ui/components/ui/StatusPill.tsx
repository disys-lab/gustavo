type Status = "Up" | "Down" | "Unknown" | string;

const VARIANT_MAP: Record<string, string> = {
  Up: "bg-green-100 text-green-800 border-green-200",
  Down: "bg-red-100 text-red-800 border-red-200",
  Unknown: "bg-yellow-100 text-yellow-800 border-yellow-200",
};

export function StatusPill({ status }: { status: Status }) {
  const cls = VARIANT_MAP[status] ?? VARIANT_MAP.Unknown;
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-semibold ${cls}`}
    >
      {status === "Up" && (
        <span className="relative flex h-2 w-2">
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-500 opacity-75" />
          <span className="relative inline-flex rounded-full h-2 w-2 bg-green-600" />
        </span>
      )}
      {status}
    </span>
  );
}
