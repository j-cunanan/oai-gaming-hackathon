# Prepared unit scene — trigger observed by investigator, verifier timed out

This fresh MAX attempt imported the explicitly operator-prepared healthy save through Load Game. The three Dagger units and empty connected conveyor route were present in normal Sandbox gameplay. It selected the middle Dagger, chose the visible **Enter Payload Block** command and assigned the leftmost conveyor as its target. Later investigator screenshots show the two untouched units and an empty route/output after an extended wait. The investigator also explored direct control; that alternate entry was not established.

**No independent verdict or fresh replay confirmation was completed.** The final independent sequence-verification request timed out. The case is **FAILED**, with no saved reproduction or proposed patch. These images are promising investigative evidence, not a qualified bug reproduction or an AI-fix result.

The old client used a 90-second request timeout and one automatic retry. The verification started after the observation at 19:42:58 UTC and the timeout failure was recorded at 19:45:59 UTC. The old implementation did not retain the investigator's final proposed oracle before requesting verification; this package therefore does not reconstruct or attribute an oracle to that model call. All 44 executed desktop actions and their checkpoint screenshots remain in the activity log.

The package preserves **191 events and 94 artifacts**. Returned-response usage is **91 model calls, 3,171,654 input tokens and 23,763 output tokens**. Timed-out requests did not return usage and are excluded from those totals; they are not a complete billing audit.

A later runner change increases the bounded request timeout, disables automatic retries, and saves future unverified trigger proposals before independent verification. Any later fresh attempt remains separate. The provided scene itself was already audited for healthy initial objects; its construction is not an AI result.

```bash
uv run repro import-evidence docs/evidence/overnight-2026-09-15/md-12565-terra-prepared-03 --manifest benchmarks/candidates/MD-candidate-12565-prepared.yaml --id recorded-md-12565-prepared
```
