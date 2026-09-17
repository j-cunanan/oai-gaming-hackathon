import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";
import test from "node:test";
import { buildDemo } from "../scripts/build-demo.mjs";

test("hosted bundle preserves current positive, blocked and rejected outcomes with usable evidence", () => {
  const root = path.resolve(
    path.dirname(fileURLToPath(import.meta.url)),
    "../../..",
  );
  const temp = fs.mkdtempSync(path.join(os.tmpdir(), "repro-demo-bundle-"));
  try {
    const catalog = buildDemo(root, path.join(temp, "bundle"));
    const dir = path.join(temp, "bundle");
    const read = (id) =>
      JSON.parse(fs.readFileSync(path.join(dir, `${id}.json`), "utf8"));
    assert.equal(catalog.length, 3);
    assert.deepEqual(
      catalog.filter((c) => c.allPassed).map((c) => c.id),
      ["datapatch"],
    );
    const datapatch = read("datapatch"),
      dummy = read("target-dummy"),
      color = read("color");
    const impact = read("impact");
    assert.equal(impact.reportsInvestigated, 7);
    assert.equal(impact.attempts, 17);
    assert.equal(impact.reproduced, 3);
    assert.equal(impact.notQualified, 4);
    assert.equal(impact.validated, 1);
    assert.equal(impact.blocked, 1);
    assert.equal(impact.rejected, 1);
    assert.deepEqual(
      impact.cases.map((c) => [
        c.baselineConfirmed,
        c.baselineTotal,
        c.candidateCorrect,
      ]),
      [
        [5, 5, 5],
        [5, 5, 5],
        [5, 5, 0],
      ],
    );
    for (const c of impact.cases) {
      const source = read(c.id);
      assert.equal(c.resultSha256, source.provenance.resultSha256);
      assert.equal(c.candidateCorrect, source.candidate.successfulRuns);
      assert.equal(c.evidence, source.files.evidence);
    }
    assert.equal(datapatch.reproduction.steps.length, 30);
    assert.equal(datapatch.candidate.successfulRuns, 5);
    assert.equal(datapatch.testCounts.tests, 276);
    assert.equal(dummy.candidate.followups.length, 12);
    assert.equal(dummy.candidate.successfulRuns, 5);
    assert.equal(dummy.allPassed, false);
    assert.equal(
      dummy.checks.find((c) => c.name === "Existing tests").status,
      "fail",
    );
    assert.equal(color.candidate.successfulRuns, 0);
    assert.equal(color.reproduction.successfulRuns, 5);
    assert.equal(color.testCounts.tests, 276);
    assert.equal(
      color.candidate.outcomes.every((o) => o.fixed === false),
      true,
    );
    for (const d of [datapatch, dummy, color]) {
      const validationStart = d.milestones
        .filter((m) => m.state === "VALIDATING")
        .at(-1).eventSeq;
      assert.equal(d.candidate.outcomes.length, 5);
      assert.ok(
        d.candidate.outcomes.every((o) => o.eventSeq > validationStart),
      );
      assert.ok(d.candidate.frames.every((f) => f.eventSeq > validationStart));
      assert.ok(d.assistance.length > 50);
      assert.ok(
        fs
          .readFileSync(path.join(dir, d.files.pdf))
          .subarray(0, 5)
          .equals(Buffer.from("%PDF-")),
      );
      assert.equal(
        fs.readFileSync(path.join(dir, d.files.patch), "utf8"),
        d.patch,
      );
      for (const [name, hash] of Object.entries(d.provenance.assets)) {
        const actual = createHash("sha256")
          .update(fs.readFileSync(path.join(dir, name)))
          .digest("hex");
        assert.equal(actual, hash);
      }
      for (const frame of [...d.baseline.frames, ...d.candidate.frames]) {
        assert.equal(d.provenance.assets[frame.url], frame.sha256);
        assert.ok(!frame.log || d.provenance.assets[frame.log]);
      }
      for (const c of d.checks)
        assert.ok(!c.artifact || d.provenance.assets[c.artifact]);
    }
    assert.ok(
      fs
        .readdirSync(dir)
        .every(
          (name) =>
            /^(?:catalog|impact|datapatch|target-dummy|color)\.json$/.test(
              name,
            ) || /^[a-f0-9]{64}\.[a-z]+$/.test(name),
        ),
    );
  } finally {
    fs.rmSync(temp, { recursive: true, force: true });
  }
});
