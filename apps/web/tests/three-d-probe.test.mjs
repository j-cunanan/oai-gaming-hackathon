import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import test from "node:test";
import { buildProbe } from "../scripts/build-probe.mjs";

test("3D probe preserves the distinct trials, recorded evidence and reference correction", () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), "repro-3d-"));
  try {
    const manifest = buildProbe(dir);
    assert.equal(manifest.runs.length, 3);
    assert.equal(manifest.control_calls, 39);
    assert.equal(manifest.verification_calls, 6);
    assert.match(manifest.scope, /Synthetic/);
    assert.match(manifest.scope, /Not included in real bug/);
    const starts = new Set();
    for (const run of manifest.runs) {
      const source = JSON.parse(
        fs.readFileSync(path.join(dir, "runs", run.id, "summary.json"), "utf8"),
      );
      assert.deepEqual(run.summary, source);
      starts.add(`${source.initial_state.x}/${source.initial_state.heading}`);
      assert.equal(source.observed_by_private_evaluator, true);
      assert.equal(source.baseline_replays, 5);
      assert.equal(source.reference_correct_replays, 5);
      for (const check of run.verification) {
        assert.equal(check.evaluator_state_supplied, false);
        assert.equal(check.investigator_conclusion_supplied, false);
        assert.equal(check.source, "repro.agents.oracle.verify_sequence");
        assert.equal(check.verdict.expected_state_reached, true);
        assert.equal(check.verdict.observed, check.variant === "seeded bug");
        assert.equal(
          check.verdict.symptom_absent,
          check.variant !== "seeded bug",
        );
        check.checkpoints.forEach((c) =>
          assert(fs.existsSync(path.join(dir, "runs", run.id, c.image))),
        );
      }
    }
    assert.equal(starts.size, 3);
    assert(fs.statSync(path.join(dir, "astra-3d-replay.mp4")).size > 1000);
  } finally {
    fs.rmSync(dir, { recursive: true, force: true });
  }
});
