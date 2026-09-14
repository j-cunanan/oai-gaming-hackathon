export type ActivityEntry = {
  seq: number;
  created_at: string;
  kind: string;
  stage: string;
  summary: string;
  artifacts: { id: string; label: string }[];
  attention: boolean;
};
export type Stage = {
  key: string;
  label: string;
  first_at: string | null;
  last_at: string | null;
  event_count: number;
  log_count: number;
};
export type ActivitySnapshot = {
  case_id: string;
  stages: Stage[];
  events: ActivityEntry[];
  last_seq: number;
  total_events: number;
};

export function mergeActivity(
  previous: ActivitySnapshot | null,
  incoming: ActivitySnapshot,
) {
  if (!previous || previous.case_id !== incoming.case_id) return incoming;
  if (incoming.last_seq <= previous.last_seq) return previous;
  const entries = new Map(previous.events.map((event) => [event.seq, event]));
  incoming.events.forEach((event) => entries.set(event.seq, event));
  return {
    ...incoming,
    events: [...entries.values()].sort((a, b) => a.seq - b.seq),
  };
}

export function filterActivity(
  events: ActivityEntry[],
  query: string,
  includeModel: boolean,
) {
  const text = query.trim().toLowerCase();
  return events.filter(
    (event) =>
      (includeModel || !["model_call", "observation"].includes(event.kind)) &&
      (!text ||
        `${event.stage} ${event.kind} ${event.summary} ${event.created_at}`
          .toLowerCase()
          .includes(text)),
  );
}

export function clockTime(value: string) {
  return new Date(value).toLocaleTimeString(undefined, {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false,
  });
}
export function dateTime(value: string) {
  return new Date(value).toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false,
  });
}
