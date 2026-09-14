# Paced wheel input — actual Arc SDL delivery checks

The prepared-unit recording and a later fresh replay showed different camera zoom levels, causing the replay's selection click to miss. This prompted a delivery probe using the **unchanged Arc SDL backend bundled in the retained historical Mindustry JAR**, inside the isolated Xvfb worker. These are infrastructure checks, not game-bug reproductions or fresh AI verdicts.

Arc's [keyboard scroll axis](https://github.com/Anuken/Arc/blob/f2398c03e5/arc-core/src/arc/input/KeyboardDevice.java#L59) stores the most recent wheel value for each update and clears it afterward. Several wheel events delivered within the same update can therefore produce one axis value. The game's camera consumes that axis. This supplies a mechanism consistent with the observed zoom mismatch; the original recording does not retain enough frame-level input data to prove the exact grouping of its wheel events.

## Delivery comparison

`delivery-comparison/` runs the existing burst of eight PyAutoGUI detents and a prototype with eight separate calls, each preserving the driver's 0.12-second PyAutoGUI pause. Each mode was sampled three times with **16, 50 and 100 milliseconds of sleep in the application update loop**. These are configured update sleeps, not measured or guaranteed frame rates.

All 18 samples received eight native wheel events. The burst samples consumed fewer than eight units through the frame-based scroll axis. All nine separately paced samples consumed exactly the requested eight units. The raw logs retain event counts and the frame in which each axis value was consumed.

## Production worker verification

`production-rpc/` repeats nine samples through the **actual rebuilt protocol-4 worker RPC**, using the production `DockerSandbox.action` and `worker.action`, with both scroll directions. Every sample received eight events and consumed exactly the requested signed total. The result binds the worker image, historical JAR, production source and exact probe sources by hash.

Protocol 4 sends one wheel detent per call and preserves the existing 0.12-second pause between calls. Short action-sequence budgets now include that deliberate pacing. This takes longer than a single burst; it improves delivery reliability at the tested update rates. It does not guarantee frame-exact input under slower or irregular rendering, or retroactively validate old recorded coordinates.

No model requests were made by these probes. The Java harness observes the real backend's input axis without changing its implementation. The Python drivers are unchanged copies of the executed scripts. An earlier local probe placed the pointer outside the centered window and received no wheel events; it was rejected before this comparison and is not included in its 18 samples. The successful runs explicitly require all eight native events before accepting a sample.

All files and raw logs are listed in `SHA256SUMS`. Historical REPRO case packages retain their original worker provenance; this driver change does not alter their saved outcomes.
