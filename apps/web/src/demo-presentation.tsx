import { useState } from "react";
import {
  ArrowLeftRight,
  ArrowRight,
  Check,
  ExternalLink,
  Layers3,
  Sparkles,
} from "lucide-react";
import type { DemoDetail, DemoImpact, DemoStage } from "./demo-model";
import "./demo-presentation.css";

export function OpenAIStageNote({
  stage,
  live,
  detail,
}: {
  stage: DemoStage;
  live: boolean;
  detail: DemoDetail | null;
}) {
  const notes: Record<DemoStage, { ai: string; runner: string }> = {
    report: live
      ? {
          ai: "Responses API + Structured Outputs turn your report into proposed actions, evidence checkpoints and missing details.",
          runner:
            "Validates the plan's structure. Planning does not execute the game or confirm the bug.",
        }
      : {
          ai: "No OpenAI call for this lookup. The selected recordings contain earlier OpenAI investigations.",
          runner:
            "Matches report terms or an exact issue link in your browser, then loads the saved evidence.",
        },
    reproduce: {
      ai:
        detail?.id === "color"
          ? "OpenAI checks the ordered screenshots against the reported symptom. This case uses an operator-supplied action trace."
          : detail?.id === "target-dummy"
            ? "OpenAI reads screenshots and chooses game-control tool calls. REPRO confirms this crash from the process exit and log signature."
            : "OpenAI reads screenshots and chooses game-control tool calls. A separate verification call checks the recorded state changes.",
      runner:
        "Records actions and checkpoints, then replays the frozen trigger on five fresh game profiles.",
    },
    reduce: {
      ai:
        detail?.id === "color"
          ? "No reduction was attempted for this case. OpenAI verified the unchanged, supplied 29-action trace."
          : detail?.id === "target-dummy"
            ? "OpenAI proposes a shorter subsequence of the recorded actions. The crash check uses process state and logs."
            : "OpenAI proposes a shorter subsequence of the recorded actions and judges whether replay still shows the symptom.",
      runner:
        detail?.id === "color"
          ? "Keeps the supplied trigger unchanged for confirmation and candidate comparison."
          : "Checks the proposal, tries bounded deletions, and requires fresh confirmation before keeping a shorter trigger.",
    },
    localize: {
      ai: "OpenAI uses source-search and file-reading tools to connect the observed failure to a likely cause in the code.",
      runner:
        "Pins the historical game revision and keeps later developer fixes out of the supplied source context.",
    },
    patch: {
      ai: "OpenAI proposes the source diff, explains why it should work, and records risks for review.",
      runner:
        "Applies the candidate in a disposable source workspace. Validation decides whether the proposal progresses.",
    },
    validate: {
      ai:
        detail?.id === "target-dummy"
          ? "OpenAI checks follow-up screenshots for the expected behavior after the fix. Baseline crash confirmation uses process state and logs."
          : "Separate OpenAI calls judge ordered screenshots for the original symptom and the expected behavior after the fix.",
      runner:
        "Builds, runs existing tests, repeats the original trigger and checks startup. All five gates must pass.",
    },
    handoff: {
      ai: "The handoff includes the saved OpenAI findings, patch explanation and visual verdicts. Export makes no new model call.",
      runner:
        "Packages the replay, evidence and PDF. A developer reviews the candidate before handoff.",
    },
  };
  const note = notes[stage];
  return (
    <aside className="demo-ai-note" aria-label="OpenAI contribution">
      <div className="demo-ai-label">
        <Sparkles size={17} />
        <strong>OpenAI at this stage</strong>
        <small>
          {stage === "report"
            ? live
              ? "Live · on request"
              : "Recorded lookup"
            : "Role in the recorded run"}
        </small>
      </div>
      <p>{note.ai}</p>
      <p>
        <strong>REPRO checks</strong>
        {note.runner}
      </p>
    </aside>
  );
}

export function ImpactPage({
  data,
  error,
  onCase,
  onArchitecture,
}: {
  data: DemoImpact | null;
  error: string;
  onCase: (id: string) => void;
  onArchitecture: () => void;
}) {
  if (!data)
    return (
      <section className="pitch-page">
        <h2>Impact</h2>
        <p role={error ? "alert" : "status"}>
          {error || "Loading verified results…"}
        </p>
      </section>
    );
  return (
    <section className="pitch-page impact-page" aria-label="Recorded impact">
      <header className="pitch-heading">
        <div>
          <span className="eyebrow">IMPACT / RETAINED MINDUSTRY RESULTS</span>
          <h2>Reported bugs. Repeatable evidence.</h2>
        </div>
        <span className="pitch-provenance">September 15, 2026 · recorded</span>
      </header>
      <div className="impact-metrics">
        {[
          [
            data.reportsInvestigated,
            "Player reports investigated",
            `${data.attempts} attempts, including guided retries`,
          ],
          [
            data.reproduced,
            "Distinct bugs reproduced",
            "Five fresh confirmations for each selected case",
          ],
          [
            data.validated,
            "AI candidate fully validated",
            "All five gates passed; human review pending",
          ],
          [
            data.rejected,
            "Ineffective candidate rejected",
            "Existing tests passed; the game scenario failed",
          ],
        ].map(([value, label, note]) => (
          <div key={label}>
            <strong>{value}</strong>
            <span>{label}</span>
            <small>{note}</small>
          </div>
        ))}
      </div>
      <div className="impact-outcomes">
        <table>
          <caption>Evidence behind the three reproduced bugs</caption>
          <thead>
            <tr>
              <th>Reported bug</th>
              <th>Baseline bug seen</th>
              <th>Correct after AI patch</th>
              <th>Decision</th>
              <th>
                <span className="sr-only">Evidence</span>
              </th>
            </tr>
          </thead>
          <tbody>
            {data.cases.map((c) => (
              <tr key={c.id}>
                <th>
                  <strong>{c.title}</strong>
                  <small>Mindustry #{c.issue}</small>
                </th>
                <td>
                  {c.baselineConfirmed}/{c.baselineTotal}
                </td>
                <td>
                  {c.candidateCorrect}/{c.candidateTotal}
                  <small>
                    {c.testCounts
                      ? `${c.testCounts.tests - c.testCounts.failures - c.testCounts.errors - c.testCounts.skipped}/${c.testCounts.tests} existing tests passed`
                      : "Upstream test archive unavailable"}
                  </small>
                </td>
                <td>
                  <span
                    className={`demo-outcome ${c.allPassed ? "passed" : "blocked"}`}
                  >
                    {c.allPassed
                      ? "Validated"
                      : c.candidateCorrect === c.candidateTotal
                        ? "Blocked"
                        : "Rejected"}
                  </span>
                </td>
                <td>
                  <button
                    className="impact-evidence"
                    onClick={() => onCase(c.id)}
                    aria-label={`View evidence for ${c.title}`}
                  >
                    View evidence <ArrowRight size={15} />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="impact-context">
        <p>
          <strong>{data.notQualified} other reports remain unqualified.</strong>{" "}
          {data.blocked} candidate passes the game replay but is blocked by an
          unavailable upstream test dependency. Repeated attempts are counted
          separately from bugs.
        </p>
        <p>
          <Sparkles size={16} />
          <span>
            <strong>OpenAI contribution</strong> Terra drove investigations,
            proposed patches and judged visual evidence. These counts are
            computed from saved records; opening this page makes no model call.
          </span>
        </p>
      </div>
      <footer className="pitch-footer">
        <details className="impact-sources">
          <summary>Scope, human guidance and source records</summary>
          <p>
            {data.scope} This is a curated development run, not a general
            success-rate estimate. QA time saved has not been measured.
          </p>
          {data.cases.map((c) => (
            <p key={c.id}>
              <a href={c.evidence} target="_blank" rel="noreferrer">
                {c.title} <ExternalLink size={12} />
              </a>{" "}
              — {c.assistance}
            </p>
          ))}
          <a href={data.ledger.url} target="_blank" rel="noreferrer">
            Inspect the {data.attempts}-attempt ledger{" "}
            <ExternalLink size={12} />
          </a>
        </details>
        <button className="button primary" onClick={onArchitecture}>
          How it works <ArrowRight size={16} />
        </button>
      </footer>
    </section>
  );
}

export function ArchitecturePage({ onDemo }: { onDemo: () => void }) {
  const [showOpenAI, setShowOpenAI] = useState(false);
  return (
    <section
      className="pitch-page architecture-page"
      aria-label="REPRO architecture"
    >
      <header className="pitch-heading">
        <div>
          <span className="eyebrow">
            {showOpenAI
              ? "ARCHITECTURE / OPENAI INTEGRATION"
              : "ARCHITECTURE / REPORT TO REVIEWED CANDIDATE"}
          </span>
          <h2>
            {showOpenAI ? "Where OpenAI is used" : "The investigation engine"}
          </h2>
        </div>
        <div className="architecture-heading-actions">
          <span className="pitch-provenance">
            System diagram · no execution
          </span>
          <button
            className="button secondary small architecture-detail-toggle"
            aria-pressed={showOpenAI}
            onClick={() => setShowOpenAI(!showOpenAI)}
          >
            {showOpenAI ? <Layers3 size={15} /> : <Sparkles size={15} />}
            {showOpenAI ? "System overview" : "OpenAI details"}
          </button>
        </div>
      </header>
      {showOpenAI ? <ArchitectureOpenAIRoles /> : <ArchitectureOverview />}
      <footer className="pitch-footer architecture-footer">
        <p>
          {showOpenAI
            ? "These are roles across separate API calls. Crash/log checks are deterministic, and PDF export makes no new model call."
            : "Custom function tools connect the model to the game. Visual verdicts are model judgments, retained for human review."}
          <br />
          Live report planning is a separate, non-executing entry point; the
          demo's game runs are recordings.
        </p>
        <button className="button secondary" onClick={onDemo}>
          Back to demo <ArrowRight size={16} />
        </button>
      </footer>
    </section>
  );
}

function ArchitectureOverview() {
  return (
    <>
      <div className="architecture-intake">
        <span>Player report</span>
        <ArrowRight size={17} />
        <span>React + TypeScript dashboard</span>
        <ArrowRight size={17} />
        <span>FastAPI investigation endpoint</span>
      </div>
      <div
        className="architecture-loop"
        aria-label="Adaptive investigation loop"
      >
        <article className="architecture-node openai-node">
          <span className="architecture-label">
            <Sparkles size={17} /> OPENAI
          </span>
          <h3>Responses API</h3>
          <p className="architecture-tech">GPT-5.6 Terra · Luna configurable</p>
          <ul>
            <li>Sees screenshots and action history</li>
            <li>Calls game and source-search tools</li>
            <li>Returns typed plans and verdicts</li>
          </ul>
        </article>
        <div className="architecture-exchange">
          <span>tool calls</span>
          <ArrowLeftRight size={29} />
          <span>images + results</span>
        </div>
        <article className="architecture-node controller-node">
          <span className="architecture-label">
            <Layers3 size={17} /> REPRO CONTROLLER
          </span>
          <h3>FastAPI + asyncio</h3>
          <p className="architecture-tech">OpenAI Python SDK · Pydantic</p>
          <ul>
            <li>Checks tool arguments and budgets</li>
            <li>Records actions and checkpoints</li>
            <li>Controls the investigation state</li>
          </ul>
        </article>
        <div className="architecture-exchange">
          <span>actions</span>
          <ArrowLeftRight size={29} />
          <span>frames + logs</span>
        </div>
        <article className="architecture-node worker-node">
          <span className="architecture-label">ISOLATED GAME WORKER</span>
          <h3>Mindustry in Docker</h3>
          <p className="architecture-tech">Linux · screenshot + input driver</p>
          <ul>
            <li>Click, type, screenshot and reset</li>
            <li>Historical source and build tools</li>
            <li>Fresh game profile for each replay</li>
          </ul>
        </article>
      </div>
      <div className="architecture-regression-label">
        <span />
        The discovered trigger becomes the regression test
        <span />
      </div>
      <ol
        className="architecture-validation"
        aria-label="Reproduction and validation pipeline"
      >
        <li>
          <span className="architecture-step">01 / CONTROLLED REPLAY</span>
          <h3>Freeze & reduce</h3>
          <p>
            Keep a repeatable trigger. Confirm accepted reductions on five fresh
            profiles.
          </p>
          <small>
            OpenAI proposes deletions and checks ordered visual evidence.
          </small>
        </li>
        <li>
          <span className="architecture-step">02 / SOURCE + PATCH</span>
          <h3>Propose a fix</h3>
          <p>Read the pre-fix source. Produce a diff, rationale and risks.</p>
          <small>OpenAI proposes; the workspace stays isolated.</small>
        </li>
        <li>
          <span className="architecture-step">03 / BEFORE + AFTER</span>
          <h3>Run the same test</h3>
          <p>Build, existing tests, original trigger and startup checks.</p>
          <small>
            OpenAI judges the expected state; REPRO enforces all five gates.
          </small>
        </li>
        <li>
          <span className="architecture-step">04 / DEVELOPER</span>
          <h3>Review the evidence</h3>
          <p>Replay, screenshots, logs, patch explanation and PDF.</p>
          <small>Human approval before handoff.</small>
        </li>
      </ol>
      <div className="architecture-evidence">
        <Check size={17} />
        <strong>Evidence retained throughout</strong>
        <span>SQLite events + hashed artifacts</span>
        <span>Live dashboard updates via SSE</span>
        <span>PDF and replay export</span>
      </div>
    </>
  );
}

function ArchitectureOpenAIRoles() {
  const roles = [
    {
      stage: "Report planning & triage",
      input: "Player report and available context",
      output:
        "Proposed test steps, evidence checkpoints and missing details; investigation triage normalizes the bug specification.",
    },
    {
      stage: "Game investigation",
      input: "Current screenshot, action history and tool results",
      output:
        "The next custom tool call: click, type, observe or reset. New screenshots guide the next decision.",
    },
    {
      stage: "Reproduction verdict",
      input:
        "Ordered checkpoint images, recorded inputs and the reported symptom",
      output:
        "A separate verification call judges whether the bug is visible, absent or inconclusive, citing image evidence.",
    },
    {
      stage: "Sequence reduction",
      input: "Frozen actions and the failure condition",
      output:
        "A shorter subsequence to try. REPRO preserves action order and confirms accepted reductions on fresh profiles.",
    },
    {
      stage: "Source analysis",
      input:
        "Confirmed reproduction and historical source through search/read tools",
      output:
        "Ranked files and symbols, a likely cause, supporting evidence and limitations.",
    },
    {
      stage: "Patch proposal",
      input: "Inspected source, bug specification and source findings",
      output:
        "A unified diff, explanation of why it should work, and risks for the developer to review.",
    },
    {
      stage: "Fix validation",
      input: "Original trigger, expected behavior and candidate screenshots",
      output:
        "Follow-up checks when needed, then separate visual judgments of whether the expected behavior actually occurs.",
    },
  ];
  return (
    <div className="architecture-ai-details">
      <div
        className="architecture-ai-capabilities"
        aria-label="OpenAI capabilities"
      >
        <div>
          <strong>Vision</strong>
          <span>Reads game state from screenshots</span>
        </div>
        <div>
          <strong>Function calling</strong>
          <span>Chooses tools that REPRO executes</span>
        </div>
        <div>
          <strong>Structured Outputs</strong>
          <span>Produces typed plans and verdicts</span>
        </div>
      </div>
      <p className="architecture-ai-model">
        OpenAI Python SDK + Responses API{" "}
        <span>GPT-5.6 Terra in the recorded cases · Luna configurable</span>
      </p>
      <div className="architecture-ai-table">
        <table>
          <caption>OpenAI roles throughout an investigation</caption>
          <thead>
            <tr>
              <th>Stage</th>
              <th>What OpenAI receives</th>
              <th>What OpenAI contributes</th>
            </tr>
          </thead>
          <tbody>
            {roles.map((role, index) => (
              <tr key={role.stage}>
                <th>
                  <span>{String(index + 1).padStart(2, "0")}</span>
                  {role.stage}
                </th>
                <td>{role.input}</td>
                <td>{role.output}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="architecture-ai-controls">
        <Check size={16} />
        <span>
          <strong>REPRO controls execution and acceptance.</strong> It validates
          tool arguments, enforces budgets, runs builds and replays, and
          requires all five gates plus human review before handoff.
        </span>
      </p>
    </div>
  );
}
