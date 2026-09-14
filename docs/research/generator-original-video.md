# Generator report — original video setup notes

These are operator observations of the video linked in [Mindustry issue #12603](https://github.com/Anuken/Mindustry/issues/12603), not a new REPRO reproduction. They inform the separate `MD-candidate-12603-video-guided` input. The original failed report-only attempt remains unchanged.

The [original Drive recording](https://drive.google.com/file/d/1Ikw9oJ3dS4ffMi4ViG005SJQR1KysG-m/view) was retrieved through the connected Drive reader on September 15, 2026 JST. It is titled `2026-09-06 12-49-27.mp4`: 95,296,993 bytes, 331.267 seconds, 780×438, nominal 30 fps. SHA-256: `f3f768b7547743829a01f91991e436c9a96bb57b759fe06e95f45e5ae2c18d12`.

Codex inspected 33 sampled frames and enlarged the setup and health/operation frames. Sampling was every ten seconds with FFmpeg's `fps=1/10`; times below are approximate positions in the source video. The full recording and extracted frames remain local analysis material; this note links to the reporter's original.

| Approximate time | Visible observation | Limit |
| --- | --- | --- |
| 25 s | A Payload Source configuration panel includes a search field, block choices and unit choices. | An icon grid alone does not establish the selected unit identity. |
| 35–55 s | A Steam Generator sits by resource sources; the later hover panel shows water and nonzero power output. A green flying unit is controlled and a separate payload conveyor is nearby. | Resource labels and the exact sequence should be verified again in the fresh test. The report specifies Blast Compound and water is needed for the steam variant. |
| 65 s | The generator is drawn on the payload conveyor with a visible effect. | A sampled frame does not independently prove the precise damage/death transition. |
| 105–115 s | The placed Steam Generator's hover panel shows an empty health bar, water and nonzero power output (132.0 then 330.0). | This is evidence supplied by the reporter, not our independent run. It does not alone establish invulnerability or enemy AI behavior. |

General setup facts were checked against the historical pre-fix source already used for this report: `Payload Source` is 5×5, belongs to the Units category and is sandbox-only; `Mega` has capacity for a 2×2 payload; Ctrl selects direct control, `[`/`]` pick up/drop cargo, Space pauses time, and E pauses construction. These are setup hints, not a root-cause diagnosis. The fresh manifest explicitly distinguishes them from the original report and contains no historical developer fix.

The fresh test must still establish the complete transition in its own screenshots: fueled and damaged generator, transport onto the conveyor, destruction/effect, retrieval and placement, then health and operation. Editor invulnerability, an unfinished building, normal payload drawing or an empty setup cannot count as the claimed bug.
