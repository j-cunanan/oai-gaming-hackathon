# Prepared generator attempt — transport transition not established

This Terra MAX investigation imported the explicitly operator-prepared healthy scene through Load Game and tested it in normal gameplay. It supplied the Steam Generator with Water and Blast Compound, observed **132.0 power output** and later nonfatal health loss, and controlled the supplied Mega for pickup attempts. It did not confirm a Steam Generator payload on the conveyor, a retrievable post-explosion payload or a placed generator with empty/zero health.

The final result is **INSUFFICIENT_EVIDENCE**, with no qualified reproduction or proposed patch. The additional setup reached working and damaged generator states, but the essential transport/explosion/redeployment sequence remained incomplete. It is not a negative confirmation of the bug. The earlier report-only and video-guided attempts remain separate.

This package contains **222 events and 109 artifacts**. Returned-response usage is **91 model calls, 3,292,742 input tokens and 26,189 output tokens**, using `gpt-5.6-terra` at MAX reasoning. The original player report, explicit video observations and origin of the additional healthy save remain visible in the input.

The events also retain a zero-call queue cancellation for a runner update and an early worker-image lookup failure after triage, before source preparation or gameplay. The successful preparation used the verified image digest after that lookup failure. Those administrative/preparation events are not additional game reproductions; the final gameplay result above describes the completed investigation.

```bash
uv run repro import-evidence docs/evidence/overnight-2026-09-15/md-12603-terra-prepared-03 --manifest benchmarks/candidates/MD-candidate-12603-prepared.yaml --id recorded-md-12603-prepared
```
