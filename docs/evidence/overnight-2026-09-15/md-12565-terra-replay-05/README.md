# Supplied unit trace — two inconclusive replays, then verifier timeout

This was an explicitly assisted qualification job, not a new autonomous discovery. An operator supplied the first **33 unchanged actions** from [the earlier AI recording](../md-12565-terra-prepared-03/README.md), selected its five existing RTS checkpoint labels and used a separately recorded [retained-image review](../unit-rts-retained-audit/README.md) to formulate the oracle. The original investigator's timed-out final oracle remains unknown.

The first two fresh-profile replays both returned `observed=false`, `expected_state_reached=false` and `symptom_absent=false`: the images did not establish that the intended unit entered the conveyor. A third fresh profile executed all 33 actions, but its independent MAX verification request timed out after 300 seconds and was not automatically retried. There are **zero confirmed reproductions from two completed verdicts**, plus one execution with no verdict. This is not five completed checks or evidence that the reported bug is absent.

The case is **FAILED**, with a supplied, unconfirmed reproduction object and no patch. Source diagnosis and AI patching were gated on five successful fresh confirmations and never started. A concrete visible mismatch is that the replay's pre-entry scene has a different zoom level from the retained recording; its coordinate-based selection misses and the HUD reads `[no units]`. The images establish that mismatch. They alone do not establish its cause.

The package preserves **111 events and 98 artifacts**. Two returned verifier responses account for **15,388 input tokens and 5,811 output tokens**. The timed-out request returned no usage, so these totals exclude its unknown consumption. The structured `model_request_failed` event and error artifact retain the failure without credentials.

The exact executed `qualification_driver.py` is included. `recorded-trigger-input.json` binds the original source events, selected action indices, manifest, oracle, driver, clean historical checkout, baseline JAR, copied baseline-test evidence and worker image. Preparation reused only an isolated build/dependency cache; every replay reset the game profile. Reused triage and the operator's checkpoint selection are explicit. The driver allowed up to 90 minutes within the overnight deadline, 120 model calls and 200 actions; the timeout ended this attempt much earlier. This case ran in its own disposable worker alongside the app-managed generator investigation.

```bash
uv run repro import-evidence docs/evidence/overnight-2026-09-15/md-12565-terra-replay-05 --manifest benchmarks/candidates/MD-candidate-12565-replay-guided.yaml --id recorded-md-12565-replay
```
