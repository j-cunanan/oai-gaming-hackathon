# Desktop input qualification — September 15, 2026

A Terra gameplay attempt requested Ctrl-clicks, but the worker ignored `keys` on
pointer actions. There was also no held-key operation, so sustained movement
could not be requested faithfully. This was a runner limitation, not evidence of
a Mindustry defect.

A disposable, network-disabled Xvfb desktop recorded actual X11 events in a small
window. No game or model was involved. The same requests were sent to the old and
updated workers: Ctrl-click, then W held for 300 ms.

| Worker | Ctrl present at mouse press | Measured W hold |
| --- | --- | --- |
| Prior protocol-2 image | No | 3 ms |
| Updated protocol-3 image | Yes | 431 ms |

The held time includes the driver's per-input pause; it is a bounded requested
hold, not a frame-exact game timing guarantee. The ordinary post-action settling
wait remains separate. The revised backend rejects protocol-2 images, preventing
an old worker from silently ignoring these fields.

[input-probe-old.json](input-probe-old.json) and
[input-probe-fixed.json](input-probe-fixed.json) contain the event timestamps and
exact image digests. An intermediate passing input-only image is also retained in
[input-probe-fixed-before-protocol-bump.json](input-probe-fixed-before-protocol-bump.json).
The [probe](probe_inputs.py) must be executed inside a disposable worker after its
Xvfb/Openbox readiness check, with a writable `/workspace/runtime`; it does not
run on the host desktop. Probe containers were removed after testing.

Unit tests also cover modifier release on exceptions, invalid-key rejection,
legacy momentary hotkeys, timing bounds and the protocol handshake. This input
qualification does not reproduce either gameplay bug or establish a game fix.
