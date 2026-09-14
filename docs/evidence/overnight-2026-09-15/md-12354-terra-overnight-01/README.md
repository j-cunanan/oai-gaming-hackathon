# Derelict conveyor cargo — setup not completed

The initial preparation failed because JitPack did not provide the pinned Arc dependency. The retry used the exact required Arc revision, `7637600c41922c078ac6bde26953ef1e71746f35`, as an isolated adjacent source checkout. The historical Mindustry source remained at `2c066e9c8c7e153e4eb91d730ead02e9011edd75`; preparation then succeeded. The dependency audit is retained in the case artifacts.

The MAX investigation created a controlled editor map with a Sharded core, Payload Source and Payload Conveyor. It did not configure or observe a block payload on that conveyor, convert the setup to Derelict, or perform the save/load transition. This is **INSUFFICIENT_EVIDENCE**, not a negative reproduction or an AI fix.

The package contains **194 events and 97 artifacts**. Cumulative usage is **91 calls, 5,771,192 input tokens and 13,457 output tokens**; this includes the original triage call. The retry lasted **846.64 seconds**. Many calls inspected historical source while trying to establish the setup. These costs are retained rather than presented as an efficient successful run.

The reporter's data-export attachment was not installed for this attempt. It was retrieved afterward for separate fixture analysis. Any future run supplied with files from that archive must be labeled separately.

```bash
uv run repro import-evidence docs/evidence/overnight-2026-09-15/md-12354-terra-overnight-01 --manifest benchmarks/candidates/MD-candidate-12354.yaml --id recorded-md-12354
```

Importing this recording verifies artifact hashes and makes no model calls.
