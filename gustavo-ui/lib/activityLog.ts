export type ActivityLevel = "info" | "success" | "error";

export interface ActivityEntry {
  id: string;
  level: ActivityLevel;
  title: string;
  description?: string;
  timestamp: Date;
}

type Listener = (entries: ActivityEntry[]) => void;

const MAX_ENTRIES = 100;
let entries: ActivityEntry[] = [];
const listeners = new Set<Listener>();

function notify() {
  const snapshot = [...entries];
  listeners.forEach((l) => l(snapshot));
}

export function addActivity(
  level: ActivityLevel,
  title: string,
  description?: string,
): ActivityEntry {
  const entry: ActivityEntry = {
    id: `${Date.now()}-${Math.random().toString(36).slice(2)}`,
    level,
    title,
    description,
    timestamp: new Date(),
  };
  entries = [entry, ...entries].slice(0, MAX_ENTRIES);
  notify();
  return entry;
}

export function clearActivity() {
  entries = [];
  notify();
}

export function subscribeActivity(listener: Listener): () => void {
  listeners.add(listener);
  listener([...entries]);
  return () => listeners.delete(listener);
}

export function getActivity(): ActivityEntry[] {
  return [...entries];
}
