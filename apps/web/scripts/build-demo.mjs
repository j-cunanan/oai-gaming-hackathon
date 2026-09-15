/** Publish selected, checksum-verified evidence with the frontend. No game or API calls. */
import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const defaultRoot = path.resolve(
  path.dirname(fileURLToPath(import.meta.url)),
  "../../..",
);
const digest = (raw) => createHash("sha256").update(raw).digest("hex");
const json = (file) => JSON.parse(fs.readFileSync(file, "utf8"));
const same = (a, b) => JSON.stringify(a) === JSON.stringify(b);

export function buildDemo(
  repoRoot = defaultRoot,
  output = path.join(repoRoot, "apps/web/public/demo"),
) {
  const config = json(path.join(repoRoot, "apps/web/demo/catalog.json"));
  // This directory contains only regenerated presentation assets.
  assert(
    path.resolve(output) !== path.resolve(repoRoot),
    "Output must not be the repository root",
  );
  fs.rmSync(output, { recursive: true, force: true });
  fs.mkdirSync(output, { recursive: true });
  const catalog = [];
  for (const entry of config) {
    const source = path.join(repoRoot, entry.package);
    const c = json(path.join(source, "result.json"));
    const events = fs
      .readFileSync(path.join(source, "events.jsonl"), "utf8")
      .trim()
      .split("\n")
      .map(JSON.parse);
    const artifacts = json(path.join(source, "artifacts.json"));
    const assets = new Map();
    const copy = (raw, ext) => {
      const name = `${digest(raw)}${ext}`;
      fs.writeFileSync(path.join(output, name), raw);
      assets.set(name, digest(raw));
      return name;
    };
    const artifact = (id) => {
      const relative = `artifacts/${id}`;
      assert(/^[\w.-]+$/.test(id), "Invalid evidence identifier");
      assert(artifacts[relative], `Missing artifact: ${id}`);
      const raw = fs.readFileSync(path.join(source, relative));
      assert.equal(
        digest(raw),
        artifacts[relative].sha256,
        `Changed evidence: ${id}`,
      );
      return { url: copy(raw, path.extname(id)), sha256: digest(raw) };
    };
    const groups = (phase) => {
      const found = [];
      let actions = [];
      for (const e of events) {
        if (e.kind === "action" && e.data.phase === phase) actions.push(e);
        if (e.kind === "replay" && e.data.phase === phase) {
          found.push({ actions, verdict: e });
          actions = [];
        }
      }
      return found;
    };
    const steps = c.reproduction.steps;
    const baseline = groups(entry.baselinePhase)
      .filter((g) =>
        same(
          g.actions.map((a) => a.data.action),
          steps,
        ),
      )
      .at(-1);
    assert(baseline, `No matching baseline for ${entry.id}`);
    assert.equal(baseline.verdict.data.verdict.observed, true);
    const followups = c.candidate_verification?.followup_steps ?? [];
    const currentValidation = events
      .filter((e) => e.kind === "state" && e.data.state === "VALIDATING")
      .at(-1);
    assert(currentValidation);
    const candidates = groups("post-patch").filter(
      (g) =>
        g.actions[0]?.seq > currentValidation.seq &&
        same(
          g.actions.map((a) => a.data.action),
          [...steps, ...followups],
        ),
    );
    assert.equal(
      candidates.length,
      5,
      `Expected five current candidate runs: ${entry.id}`,
    );
    const outcomes = events.filter(
      (e) => e.kind === "validation_replay" && e.seq > currentValidation.seq,
    );
    assert.equal(outcomes.length, 5);
    const successful = outcomes.filter((e) => e.data.fixed === true).length;
    assert.equal(
      c.checks.find((check) => check.name === "Original replay after patch")
        .status === "pass",
      successful === 5,
    );
    const frames = (group, labels) => {
      const selected = group.actions.filter((e) =>
        labels.includes(e.data.action.checkpoint),
      );
      assert.deepEqual(
        selected.map((e) => e.data.action.checkpoint),
        labels,
      );
      return selected.map((e) => ({
        ...artifact(e.data.screenshot_after),
        label: e.data.action.semantic,
        checkpoint: e.data.action.checkpoint,
        eventSeq: e.seq,
        recordedAt: e.created_at,
        process: e.data.process,
        log: e.data.log_artifact ? artifact(e.data.log_artifact).url : null,
      }));
    };
    const pdfMeta = json(path.join(repoRoot, entry.pdfProvenance));
    const pdf = fs.readFileSync(path.join(repoRoot, entry.pdf));
    assert.equal(digest(pdf), pdfMeta.pdf_sha256, "PDF checksum mismatch");
    for (const [file, sha] of Object.entries(pdfMeta.saved_case_sources))
      assert.equal(
        digest(fs.readFileSync(path.join(repoRoot, file))),
        sha,
        "PDF source changed",
      );
    const patch = fs.readFileSync(path.join(source, "candidate.patch"));
    assert.equal(
      digest(patch),
      artifacts[`artifacts/${c.patch_artifact}`].sha256,
    );
    const checks = c.checks.map((check) => ({
      ...check,
      artifact: check.artifact ? artifact(check.artifact).url : null,
      baseline_artifact: check.baseline_artifact
        ? artifact(check.baseline_artifact).url
        : null,
    }));
    const allPassed =
      checks.length === 5 && checks.every((check) => check.status === "pass");
    const status = allPassed
      ? "Validated candidate"
      : successful === 5
        ? "Validation blocked"
        : "Candidate failed";
    let testCounts = null;
    if (entry.suiteAudit) {
      const audit = json(path.join(repoRoot, entry.suiteAudit));
      assert.equal(audit.candidate_patch_sha256, digest(patch));
      assert.equal(
        audit.candidate_tests_log_artifact,
        c.checks.find((check) => check.name === "Existing tests").artifact,
      );
      assert.equal(
        audit.candidate_tests_log_sha256,
        artifacts[`artifacts/${audit.candidate_tests_log_artifact}`].sha256,
      );
      testCounts = audit.counts;
    }
    const evidenceUrl = `https://github.com/j-cunanan/oai-gaming-hackathon/tree/main/${entry.package}`;
    const detail = {
      id: entry.id,
      caseId: c.id,
      title: entry.title,
      recordedAt: c.updated_at,
      report: c.report,
      summary: entry.summary,
      targetCommit: c.report.target_commit,
      status,
      allPassed,
      modelNote: entry.modelNote,
      assistance: entry.assistance,
      scope: entry.scope,
      reductionNote: entry.reductionNote,
      usage: c.usage,
      elapsedSeconds: c.elapsed_seconds,
      firstReproducedSeconds: c.first_reproduced_seconds,
      reproduction: {
        successfulRuns: c.reproduction.successful_runs,
        totalRuns: c.reproduction.total_runs,
        originalActions: c.reproduction.original_actions,
        steps,
        oracle: c.reproduction.oracle,
      },
      baseline: {
        phase: entry.baselinePhase,
        verdict: baseline.verdict.data.verdict,
        frames: frames(baseline, c.reproduction.oracle.checkpoints),
      },
      candidate: {
        successfulRuns: successful,
        totalRuns: outcomes.length,
        followups,
        verdict: candidates[0].verdict.data.verdict,
        frames: frames(
          candidates[0],
          c.candidate_verification?.oracle.checkpoints ??
            c.reproduction.oracle.checkpoints,
        ),
        outcomes: outcomes.map((e) => ({
          recordedAt: e.created_at,
          eventSeq: e.seq,
          ...e.data,
          screenshot: artifact(e.data.screenshot).url,
        })),
      },
      findings: c.findings,
      patch: patch.toString("utf8"),
      rationale: c.patch_rationale,
      checks,
      testCounts,
      milestones: events
        .filter((e) => e.kind === "state")
        .map((e) => ({ recordedAt: e.created_at, eventSeq: e.seq, ...e.data })),
      files: {
        pdf: copy(pdf, ".pdf"),
        patch: copy(patch, ".patch"),
        replay: copy(fs.readFileSync(path.join(source, "repro.yaml")), ".yaml"),
        evidence: evidenceUrl,
      },
      provenance: {
        resultSha256: digest(fs.readFileSync(path.join(source, "result.json"))),
        eventsSha256: digest(
          fs.readFileSync(path.join(source, "events.jsonl")),
        ),
        artifactsSha256: digest(
          fs.readFileSync(path.join(source, "artifacts.json")),
        ),
        assets: Object.fromEntries(assets),
      },
    };
    fs.writeFileSync(
      path.join(output, `${entry.id}.json`),
      JSON.stringify(detail, null, 2) + "\n",
    );
    catalog.push({
      id: entry.id,
      title: entry.title,
      issue: entry.issue,
      summary: entry.summary,
      sampleReport: entry.sampleReport,
      game: "mindustry",
      caseId: c.id,
      status,
      allPassed,
      matching: entry.matching,
      negativePatterns: entry.negativePatterns,
    });
  }
  fs.writeFileSync(
    path.join(output, "catalog.json"),
    JSON.stringify(catalog, null, 2) + "\n",
  );
  return catalog;
}

if (
  process.argv[1] &&
  path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)
) {
  const catalog = buildDemo();
  console.log(
    `Bundled ${catalog.length} recorded cases with verified evidence, reports and replay files.`,
  );
}
