# Report-driven demo in the REPRO app

Open **Report demo** in the app, or visit `/?view=demo`. A connected backend offers **Live AI plan** and **Recorded cases**. Static hosting offers the recorded flow only. In Recorded cases, paste a player report or an exact Mindustry issue URL, inspect the suggested match and choose **Review recorded case**. Example reports are available for data-patch persistence, the Target Dummy save crash and color readback.

## Live report planning

**Map the test with AI** makes one new OpenAI Responses API request for a Mindustry report. It proposes a visual sequence of setup, action and evidence checkpoints, the expected behavior, missing details and assumptions. The model receives the report and a small catalog of report descriptions. It does not receive screenshots, source, patches or saved validation results. Optional pointers to prior recordings are AI suggestions, not evidence that this new report is the same bug.

The plan is explicitly **not executed**. It does not start Docker, create a case, reproduce a bug or modify existing evidence. A fresh investigation is a separate, explicit action. Every successful plan records its input hash, timestamp, actual model, elapsed request time, usage and result under `.repro/report-plans/` (or the configured data directory). Those local files are not bundled into the website. The UI shows the actual generated plan, with no simulated progress or cached response presented as live.

`POST /api/report-plan` accepts a 10–8,000-character report, allows one in-flight planning request, uses the configured model with low reasoning and a 2,600-token output ceiling, disables automatic retries and has a 50-second overall timeout. Incomplete/refused/malformed responses cannot become plans. The standard same-origin mutation guard applies. Report text is sent to OpenAI only when the user requests live planning. Static recording matching continues to keep report text in the browser.

**Presentation view**, or `/?view=demo&present=1`, hides workspace navigation and retains the live/recorded provenance labels. All recorded stage links accept `present=1`. If the API is unavailable, use Recorded cases without implying a new model or game run. A URL alone is enough for the existing rule matcher, but live planning needs the report text and does not fetch arbitrary links.

The walkthrough follows **Report → Reproduce → Reduce → Diagnose → Patch → Validate → Handoff**. Each stage presents actual saved evidence: screenshots and event timestamps, the frozen input sequence, source findings, patch rationale and diff, all five validation gates, and downloadable PDF, YAML and patch files. The data-patch candidate passes; Target Dummy has an upstream-test blocker; the color candidate fails its replay checks. Browsing never changes those outcomes or creates a new case.

Report matching is a small, explicit browser-side matcher over this three-case catalog. It recognizes affected features, symptoms, workflow terms and exact upstream issue links. It supports the tested paraphrases, exposes missing details, and keeps multiple suggestions when a report describes multiple behaviors. It is not an AI classifier, fresh triage, or evidence that an incoming report is the same bug. Unrelated reports have no match. Text entered for matching stays in the browser. A visitor explicitly chooses the recorded case before viewing it.

When a backend is connected, an unmatched report or the final handoff step can open **New investigation** with the report prefilled. A selected historical target revision is prefilled for review, and can be changed. Creating that case remains a separate action. Report matching never passes source findings, candidate diffs or evaluator-only material into a new investigation. The normal new-investigation form also offers **Find a recorded case**.

## Hosting

The demo is bundled with the frontend, so it needs neither the separate docs preview server nor a game worker or API key. The checked-in `vercel.json` uses the repository root, installs the web app, runs the demo build and serves `apps/web/dist`. Keep the Vercel project's **Root Directory at the repository root**: the build reads the checked-in evidence under `docs/`. Use Node.js 22 or later. The configuration uses Vercel's documented [build and output settings](https://vercel.com/docs/project-configuration/vercel-json).

For a static host other than Vercel:

```bash
npm --prefix apps/web ci
VITE_REPRO_MODE=demo npm --prefix apps/web run build
# Publish apps/web/dist as the website root.
```

`VITE_REPRO_MODE=demo` makes the report flow the landing page and disables backend requests and live-workspace controls. Only the generated frontend output should be hosted. A regular build without that setting retains the connected application and its `/?view=demo` route. The static deployment does not run fresh game investigations; those use the existing FastAPI backend and Linux worker. No live backend URL or deployment credentials are embedded in this build.

The route uses query parameters, so it works on an ordinary static server without a route-rewrite service. For example, `/?view=demo&demo=datapatch&stage=validate` opens the saved validation stage. **Copy stage link** preserves the case and stage, without including the visitor's pasted report. An unavailable case link returns to intake with an explanation.

## Evidence packaging

`apps/web/scripts/build-demo.mjs` builds the presentation from the frozen snapshots specified in `apps/web/demo/catalog.json`. The script:

- Selects a baseline replay whose complete action list matches the stored trigger.
- Selects five candidate runs from the latest validation attempt, checking the unchanged trigger and any separately frozen follow-up actions.
- Verifies screenshot/log/patch hashes, PDF provenance, and the association between a test-suite audit and the candidate patch and log.
- Copies only selected evidence into the generated `apps/web/public/demo` directory, then includes it in the frontend build. The original full snapshot remains in the repository.
- Derives passing, blocked and failed states from the recorded checks and verdicts. It does not replace failed gates or invent unrecorded actions.

The generated bundle is about 9 MB for all three cases. Case JSON and screenshots load when selected. Playback advances selected screenshots every 2.5 seconds and is labeled as a recorded excerpt; real execution duration and cumulative model usage remain visible separately. Original operator assistance and evidence limits are included throughout the walkthrough.

The matcher and bundle have automated tests for paraphrases, ambiguity, missing prerequisites, unrelated/healthy/other-game reports, current-attempt selection, rejected candidates and asset integrity. The existing workspace still has its normal backend validation and approval gates.
