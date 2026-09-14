# Review of a retained RTS recording — not a fresh replay

This is a later, separately recorded Terra MAX review of five existing screenshots from [the prepared-scene investigation](../md-12565-terra-prepared-03/README.md). An operator selected its existing checkpoint labels at action indices **27, 28, 29, 30 and 33**, supplied with the complete first 33 recorded actions. The original investigator's timed-out final oracle is unknown. This review does not reconstruct that oracle, change the original **FAILED** result or constitute a fresh game execution.

The reviewer returned `observed=true`, `expected_state_reached=true`, `symptom_absent=false`, with confidence **0.87**. It interpreted the selected sequence as a visible unit assigned the Enter Payload Block command, followed by an empty intake/route and a command HUD reporting no selected units. Screenshots cannot establish the internal entity/payload state or the untested manual-control path. This is a model judgment about selected retained evidence, not five fresh confirmations.

`audit.json` contains the exact reviewed oracle, complete supplied trace, verdict and source hashes. `audit-events.jsonl` records the separate request. It used **one returned model call, 7,682 input tokens and 10,477 output tokens**, at MAX reasoning with a 300-second request timeout and no automatic retry. The original screenshots remain in their original evidence package and are referenced by exact hash.

`audit_driver.py` is an unchanged copy of the executed local driver; `source-paths.json` maps its original local path to this committed copy. The driver expects the original repository-relative paths and writes a new local audit directory. Re-running it would make a new paid request; the files here are the completed result, not instructions to repeat it.

The selected trace was subsequently supplied as explicit assistance to a separate fresh-profile qualification job, `md-12565-terra-replay-05`. Only that job's actual replay results can qualify the supplied trigger for diagnosis and patching. The retained-image verdict alone cannot do so.
