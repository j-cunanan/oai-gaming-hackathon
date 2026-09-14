import assert from "node:assert/strict";
import test from "node:test";
import { preferredCase } from "../src/case-selection.ts";

const make = (id, state, updated_at = "2026-09-14T00:00:00Z", checks = []) =>
  ({ id, state, updated_at, checks });
const passing = ["Regression before patch", "Candidate build", "Existing tests",
  "Original replay after patch", "Smoke test"].map(name => ({ name, status: "pass" }));

test("prefers all five gates, then state progress, then recorded recency", () => {
  assert.equal(preferredCase([]), "");
  assert.equal(preferredCase([make("failed", "FAILED"), make("ready", "READY")]), "ready");
  assert.equal(preferredCase([make("complete", "COMPLETE"),
    make("recording", "AWAITING_HUMAN", "2026-09-13", passing)]), "recording");
  assert.equal(preferredCase([make("old", "READY", "2026-09-13"),
    make("new", "READY", "2026-09-14")]), "new");
  assert.equal(preferredCase([make("partial", "READY", "2026-09-14", passing.slice(0, 4)),
    make("advanced", "VALIDATING")]), "advanced");
});
