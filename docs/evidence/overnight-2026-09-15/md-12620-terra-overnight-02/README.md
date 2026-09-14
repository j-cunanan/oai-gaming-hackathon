# Deleted data patch returns — fresh AI fix

This evidence-guided Terra investigation started from the original report plus explicitly labeled save-checkpoint guidance. Its input did not include a human fix, future source, or diagnosis. It is separate from the earlier report-only attempt, which remains at 3/5 confirmations.

The original 31-action trace reproduced the persistence bug in **5/5** fresh profiles. The reduced 30-action trace also passed **5/5**. The AI then traced deletion through the editor, the cached asset list and save serialization, and proposed the retained one-line reload in the deletion handler.

All five gates passed: baseline regression, candidate build, **276/276 existing tests with zero skips**, **5/5 candidate replays** in which deletion persisted after reopening the same map, and startup smoke. The candidate suite used network access; gameplay and replays remained offline. No baseline failures were waived. The [JUnit supplement](../datapatch-suite-audit/) preserves the completed suite XML.

The run used `gpt-5.6-terra`, medium reasoning and protocol-3 worker `repro-worker:overnight-inputs-20260915`. Totals: **80 model calls, 926,267 input tokens and 15,071 output tokens**. It includes setup guidance and a reduction-heavy development run; these are not general benchmark rates. The case remains `AWAITING_HUMAN`; no game patch was published upstream.

`result.json`, `events.jsonl` and `artifacts.json` preserve 876 events and 339 artifact files. `repro.yaml`, `source-findings.json`, `patch-rationale.json` and `candidate.patch` are convenient sidecars. Artifact hashes cover screenshots, logs and saved model outcomes; recorded visual judgments remain model-based.

Import without Docker or model calls:

```bash
uv run repro import-evidence docs/evidence/overnight-2026-09-15/md-12620-terra-overnight-02 --manifest benchmarks/candidates/MD-candidate-12620-guided.yaml --id recorded-md-12620-guided
```

To attempt a new execution, register a new case with `repro import-case benchmarks/candidates/MD-candidate-12620-guided.yaml`, prepare its historical build and run `repro investigate CASE_ID`. This makes fresh model calls and does not guarantee the same outcome. Imported recordings themselves are read-only.
