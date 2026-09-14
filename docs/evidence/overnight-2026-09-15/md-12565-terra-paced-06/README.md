# Calibrated unit trace — selection recovered, entry still unqualified

This separate qualification used the same supplied 33-action trace and five operator-selected RTS labels as the prior replay attempt. It changed only the two scroll amounts at original action indices **10 and 11**, from `-8/-8` to `-2/-1`, to request three individually paced detents with the new protocol-4 worker. This is explicit operator input calibration, not a new autonomous discovery or an unchanged replay of the old recording.

The fresh pre-entry screenshot matches the earlier scene's zoom and shows the intended middle unit selected. The independent Terra MAX verifier nevertheless found no demonstrated entry: the outlined subject remained left of the conveyor in the later screenshots, and the route stayed empty. It returned `observed=false`, `expected_state_reached=false`, `symptom_absent=false`, confidence **0.97**.

The result is **INSUFFICIENT_EVIDENCE**, with **0/1 completed fresh confirmations**, an unconfirmed supplied replay and no patch. The job stopped after the unsuccessful verdict because its required 5/5 qualification was no longer possible. It does not establish that the game bug is absent. Source diagnosis and patching never started.

The package retains **42 events and 38 artifacts**, including freshly executed offline baseline assertions on the new worker. The historical JAR and dependency cache were reused with source/JAR checks; old-worker baseline-test results were not reused. One returned model request used **7,685 input tokens and 3,449 output tokens**. Its limits were MAX reasoning, a 16,000-token response allowance, a 450-second request timeout without automatic retry, and up to 65 minutes inside the overnight deadline; it stopped much earlier.

`qualification_driver.py` is the unchanged executed driver. The `recorded-trigger-input.json` artifact binds that driver, input manifest, source events, exact scroll changes and worker/JAR provenance. The [native input delivery checks](../../paced-scroll-2026-09-15/README.md) establish the runner change's narrower scope; they are not gameplay verdicts.

```bash
uv run repro import-evidence docs/evidence/overnight-2026-09-15/md-12565-terra-paced-06 --manifest benchmarks/candidates/MD-candidate-12565-scroll-guided.yaml --id recorded-md-12565-paced
```
