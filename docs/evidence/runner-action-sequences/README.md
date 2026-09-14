# Bounded desktop sequences — real X11 validation

`computer_sequence` lets the investigator or fix-check planner issue 2–8 known inputs without a model call between them. It keeps the ordinary per-action screenshot, log, checkpoint, wait, hold and replay entry. It returns the final screen and intermediate artifact references. Unknown navigation should still use one action at a time. The inputs are sequential, not simultaneous or frame-exact.

This infrastructure probe used the protocol-3 worker and a disposable X11 event-listener window, **not Mindustry and not an AI investigation**. It made no model calls. Four actions (Ctrl-click, a held W key, typing `repro`, and Enter) completed in one sequence call in **1.67 seconds**. Replaying the same four ordinary actions on a fresh desktop produced matching event types, keys/buttons and modifier states. Requested W hold was 300 ms; measured holds were 433 ms in the sequence and 424 ms in ordinary replay, including driver overhead. This is a functional/timing observation, not a measured end-to-end AI speedup ratio.

The probe then exited its process on Escape. Only that first action ran; subsequent typing was skipped. A new sequence against the exited process issued zero inputs. Unit tests also cover budget exhaustion, reused checkpoints and input failure before later actions. The full sequence is checked against the remaining action budget and new checkpoint labels before any input. Programmed waits, holds and typing are bounded to 20 seconds.

`result.json` binds the worker image, executed helper/recorder/probe source hashes and recorded artifact hashes. `events.jsonl` retains each ordinary action and the sequence audit. The X11 files retain native input events from the sequence and fresh replay. `probe.py` is an unchanged copy of the executed local driver; its original execution path appears in the source hash record.

To repeat with the same already-built worker image and a new output directory:

```bash
uv run python docs/evidence/runner-action-sequences/probe.py --image repro-worker:overnight-inputs-20260915 --output .repro/new-sequence-probe
```

The probe removes only its own disposable container. Its results do not establish any gameplay bug, patch correctness or benchmark score.
