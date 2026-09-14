import assert from "node:assert/strict";
import test from "node:test";
import { filterActivity, mergeActivity } from "../src/activity-model.ts";

const event = (seq, stage = "triage", kind = "state") => ({
  seq,
  stage,
  kind,
  created_at: "2026-09-13T16:41:21Z",
  summary: "Weather controls",
  artifacts: [],
  attention: false,
});
const snapshot = (events, id = "case-a") => ({
  case_id: id,
  stages: [],
  events,
  last_seq: events.at(-1)?.seq || 0,
  total_events: events.length,
});

test("incremental history deduplicates entries and rejects stale responses", () => {
  const original = snapshot([event(1), event(4)]);
  const incoming = snapshot([event(4), event(9, "reduce")]);
  const merged = mergeActivity(original, incoming);
  assert.deepEqual(
    merged.events.map((e) => e.seq),
    [1, 4, 9],
  );
  assert.equal(mergeActivity(merged, original), merged);
  const other = snapshot([event(2)], "case-b");
  assert.equal(mergeActivity(merged, other), other);
});

test("search spans older stages and can include model calls", () => {
  const events = [
    event(1),
    event(2, "localize", "model_call"),
    event(3, "validate", "action"),
  ];
  assert.equal(filterActivity(events, "WEATHER", false).length, 2);
  assert.deepEqual(
    filterActivity(events, "triage", false).map((e) => e.seq),
    [1],
  );
  assert.deepEqual(
    filterActivity(events, "localize", true).map((e) => e.seq),
    [2],
  );
  assert.equal(filterActivity(events, "absent", true).length, 0);
});
