# First supplied color qualification — required images omitted

This is the frozen first attempt of the assisted color case. It supplies the investigator's final 29 unchanged actions after a reset, cached triage and six existing entered/confirmed/readback checkpoints. The required outcome included a placed-and-picked Colored Wall and the reopened Colored Floor picker.

The independent MAX check recognized `ff0300` input and `ff0200ff` readback on both picker paths. It returned **inconclusive** for the combined contract because the selected six screenshots did not include the wall-placement and picking transitions. Those actions were present in the full recorded trace, but their screenshots were omitted from the selected evidence. The result is `observed=false`, `expected_state_reached=false`, `symptom_absent=false`, confidence **0.87**.

The attempt stopped at **0/1 completed fresh confirmations**, with no source diagnosis or patch. This is not a negative finding about the reported color defect. It demonstrates an evidence-selection error by the operator: the verifier did not accept an unshown prerequisite from action intent alone.

The snapshot contains **38 events and 33 artifacts**. One returned request used **8,848 input tokens and 15,447 output tokens**, with MAX reasoning, a 24,000-token response allowance and a 450-second request timeout. The exact initial `qualification_driver.py` and its recorded hash are retained. Fresh baseline assertions ran on the protocol-4 worker; the clean historical compiled JAR and dependency cache were reused with explicit provenance.

The same case was subsequently continued by adding the two existing wall-placement and picking labels to the selected six. All 29 actions and the required outcome remained unchanged. That continuation starts a new five-confirmation series, retains this failed selection and uses the remaining portion of the original 55-minute time budget. Its results must be read separately from this snapshot.

```bash
uv run repro import-evidence docs/evidence/overnight-2026-09-15/md-12623-terra-replay-02-first --manifest benchmarks/candidates/MD-candidate-12623-replay-guided.yaml --id recorded-md-12623-first
```
