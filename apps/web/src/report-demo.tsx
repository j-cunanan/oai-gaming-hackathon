import { useEffect, useRef, useState } from "react";
import {
  ArrowDownToLine,
  ArrowLeft,
  ArrowRight,
  BarChart3,
  Check,
  ChevronRight,
  Copy,
  FileText,
  Link2,
  Layers3,
  LoaderCircle,
  Pause,
  Play,
  RotateCcw,
  Search,
  ShieldCheck,
} from "lucide-react";
import { PatchReview } from "./patch-review";
import { dateTime } from "./activity-model";
import { HelpTip } from "./help";
import { ReportPlanner } from "./report-planner";
import {
  ArchitecturePage,
  ImpactPage,
  OpenAIStageNote,
} from "./demo-presentation";
import type { PlanResult } from "./report-planner";
import {
  demoLocation,
  demoSection,
  demoStages,
  matchReport,
} from "./demo-model";
import type {
  DemoAction,
  DemoDetail,
  DemoFrame,
  DemoImpact,
  DemoSection,
  DemoStage,
  DemoSummary,
  ReportMatch,
} from "./demo-model";
import "./report-demo.css";

const asset = (name: string) => `${import.meta.env.BASE_URL}demo/${name}`;
const minutes = (seconds: number) =>
  `${Math.floor(seconds / 60)}m ${Math.floor(seconds % 60)}s`;

export function ReportDemo({
  initialReport = "",
  initialGame = "mindustry",
  connected,
  availableCases,
  onFreshReport,
  onOpenCase,
}: {
  initialReport?: string;
  initialGame?: string;
  connected: boolean;
  availableCases: string[];
  onFreshReport: (body: string, game: string, commit?: string) => void;
  onOpenCase: (id: string) => void;
}) {
  const initialRoute = useRef(demoLocation(window.location.search));
  const [catalog, setCatalog] = useState<DemoSummary[]>([]);
  const [report, setReport] = useState(initialReport);
  const [game, setGame] = useState(initialGame);
  const [matches, setMatches] = useState<ReportMatch[] | null>(null);
  const [selected, setSelected] = useState<string | null>(
    initialRoute.current.id,
  );
  const [stage, setStage] = useState<DemoStage>(initialRoute.current.stage);
  const [detail, setDetail] = useState<DemoDetail | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [copied, setCopied] = useState(false);
  const [intakeMode, setIntakeMode] = useState<"live" | "recorded">("live");
  const [plan, setPlan] = useState<PlanResult | null>(null);
  const [section, setSection] = useState<DemoSection>(() =>
    demoSection(window.location.search),
  );
  const [impact, setImpact] = useState<DemoImpact | null>(null);
  const [impactError, setImpactError] = useState("");
  const [presenting, setPresenting] = useState(
    () => new URLSearchParams(window.location.search).get("present") === "1",
  );
  const heading = useRef<HTMLHeadingElement>(null);
  const presentation = useRef<HTMLElement>(null);
  const index = demoStages.findIndex((s) => s.id === stage);

  useEffect(() => {
    document.body.classList.toggle("repro-presenting", presenting);
    const url = new URL(window.location.href);
    if (presenting) url.searchParams.set("present", "1");
    else url.searchParams.delete("present");
    window.history.replaceState(null, "", url);
    return () => document.body.classList.remove("repro-presenting");
  }, [presenting]);

  useEffect(() => {
    const controller = new AbortController();
    fetch(asset("catalog.json"), { signal: controller.signal })
      .then(async (r) => {
        if (!r.ok)
          throw new Error(
            "The recorded case catalog could not be loaded. Reload to retry.",
          );
        setCatalog(await r.json());
      })
      .catch((e) => {
        if (!controller.signal.aborted) setError(e.message);
      });
    return () => controller.abort();
  }, []);
  useEffect(() => {
    const controller = new AbortController();
    fetch(asset("impact.json"), { signal: controller.signal })
      .then(async (r) => {
        if (!r.ok)
          throw new Error(
            "The recorded impact summary could not be loaded. Reload to retry.",
          );
        setImpact(await r.json());
      })
      .catch((e) => {
        if (!controller.signal.aborted) setImpactError(e.message);
      });
    return () => controller.abort();
  }, []);
  useEffect(() => {
    const pop = () => {
      const route = demoLocation(window.location.search);
      setSelected(route.id);
      setStage(route.stage);
      setSection(demoSection(window.location.search));
    };
    window.addEventListener("popstate", pop);
    return () => window.removeEventListener("popstate", pop);
  }, []);
  useEffect(() => {
    if (!catalog.length) return;
    setDetail(null);
    if (!selected) {
      setLoading(false);
      setStage("report");
      return;
    }
    if (!catalog.some((c) => c.id === selected)) {
      setError(
        "That recorded case is unavailable. Paste a report or choose an example.",
      );
      setSelected(null);
      setStage("report");
      return;
    }
    const controller = new AbortController();
    setLoading(true);
    setError("");
    fetch(asset(`${selected}.json`), { signal: controller.signal })
      .then(async (r) => {
        if (!r.ok)
          throw new Error(
            "The recorded evidence could not be loaded. Choose the case again to retry.",
          );
        const data = (await r.json()) as DemoDetail;
        if (data.id !== selected)
          throw new Error("The recording does not match the selected case.");
        setDetail(data);
      })
      .catch((e) => {
        if (!controller.signal.aborted) setError(e.message);
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [selected, catalog]);
  useEffect(() => {
    const url = new URL(window.location.href);
    url.searchParams.set("view", "demo");
    url.searchParams.delete("case");
    if (section === "demo") url.searchParams.delete("section");
    else url.searchParams.set("section", section);
    if (selected) {
      url.searchParams.set("demo", selected);
      url.searchParams.set("stage", stage);
    } else {
      url.searchParams.delete("demo");
      url.searchParams.delete("stage");
    }
    window.history.replaceState(null, "", url);
    document.title =
      section === "impact"
        ? "Impact | REPRO"
        : section === "architecture"
          ? "Architecture | REPRO"
          : detail
            ? `${detail.title} · ${demoStages[index].title} | REPRO demo`
            : "Report demo | REPRO";
    setCopied(false);
  }, [selected, stage, detail, index, section]);

  function showSection(next: DemoSection) {
    setSection(next);
    presentation.current?.scrollIntoView({
      behavior: "smooth",
      block: "start",
    });
  }

  function edit(value: string) {
    setPlan(null);
    setReport(value);
    setMatches(null);
    setSelected(null);
    setDetail(null);
    setStage("report");
    setError("");
  }
  function go(next: DemoStage) {
    setStage(next);
    setTimeout(() => heading.current?.focus(), 0);
  }
  function choose(id: string) {
    setSelected(id);
    go("reproduce");
  }
  const freshBody = report || detail?.summary || "";

  return (
    <section
      ref={presentation}
      className="report-demo"
      aria-label="Report-driven demo"
    >
      <div className="demo-presentation-bar">
        <strong>
          REPRO <span>Game bug investigations</span>
        </strong>
        <nav className="demo-pitch-nav" aria-label="Presentation navigation">
          {(
            [
              { id: "demo", label: "Demo", icon: Play },
              { id: "impact", label: "Impact", icon: BarChart3 },
              { id: "architecture", label: "Architecture", icon: Layers3 },
            ] as const
          ).map((item) => (
            <button
              key={item.id}
              aria-label={item.label}
              aria-current={section === item.id ? "page" : undefined}
              onClick={() => showSection(item.id)}
            >
              <item.icon size={15} />
              {item.label}
              {item.id === "impact" && impact && (
                <small>{impact.reproduced} reproduced</small>
              )}
            </button>
          ))}
        </nav>
        <button
          className="button secondary small"
          aria-pressed={presenting}
          onClick={() => setPresenting(!presenting)}
        >
          {presenting ? "Exit presentation view" : "Presentation view"}
        </button>
      </div>
      {section === "impact" && (
        <ImpactPage
          data={impact}
          error={impactError}
          onArchitecture={() => showSection("architecture")}
          onCase={(id) => {
            setSelected(id);
            showSection("demo");
            go("validate");
          }}
        />
      )}
      {section === "architecture" && (
        <ArchitecturePage onDemo={() => showSection("demo")} />
      )}
      <div className="demo-workflow" hidden={section !== "demo"}>
        <div className="demo-mode-bar">
          <span>
            <span className="tiny-dot purple" />{" "}
            {stage === "report" && connected
              ? "Report workspace"
              : "Recorded investigation"}{" "}
            <HelpTip topic="Report demo" />
          </span>
          <p>
            {stage === "report" && connected
              ? "Generate a live test plan or browse prior investigations. Game evidence comes from saved runs."
              : "Explore an actual saved run. These steps show recorded evidence and do not start a new investigation."}
          </p>
          {(detail || matches) && (
            <button className="button secondary small" onClick={() => edit("")}>
              <RotateCcw size={14} /> Start over
            </button>
          )}
        </div>
        {error && (
          <div role="alert" className="error-banner">
            {error}
          </div>
        )}
        <nav className="demo-stages" aria-label="Recorded investigation stages">
          {demoStages.map((item, i) => (
            <button
              key={item.id}
              aria-current={stage === item.id ? "step" : undefined}
              disabled={item.id !== "report" && !detail}
              onClick={() => go(item.id)}
            >
              <span>{String(i + 1).padStart(2, "0")}</span>
              <strong>{item.title}</strong>
            </button>
          ))}
        </nav>
        <OpenAIStageNote
          stage={stage}
          live={connected && intakeMode === "live"}
          detail={detail}
        />

        {stage === "report" && connected && (
          <div className="planner-mode" aria-label="Report intake mode">
            <button
              className={`button ${intakeMode === "live" ? "primary" : "secondary"}`}
              aria-pressed={intakeMode === "live"}
              onClick={() => setIntakeMode("live")}
            >
              Live AI plan
            </button>
            <button
              className={`button ${intakeMode === "recorded" ? "primary" : "secondary"}`}
              aria-pressed={intakeMode === "recorded"}
              onClick={() => setIntakeMode("recorded")}
            >
              Recorded cases
            </button>
            <p>Live planning uses OpenAI. Recorded cases work offline.</p>
          </div>
        )}

        {stage === "report" && connected && intakeMode === "live" ? (
          <ReportPlanner
            report={report}
            onEdit={edit}
            catalog={catalog}
            result={plan}
            onResult={setPlan}
            onChoose={choose}
            onFresh={() => onFreshReport(report, "mindustry")}
          />
        ) : stage === "report" ? (
          <div className="demo-intake-grid">
            <section className="panel demo-intake">
              <div className="eyebrow">01 / REPORT INTAKE</div>
              <h2 ref={heading} tabIndex={-1}>
                What did the player report?
              </h2>
              <p>
                Paste the behavior or a Mindustry issue link. REPRO looks for a
                related recorded investigation.
              </p>
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  setMatches(matchReport(report, game, catalog));
                  setError("");
                }}
              >
                <label>
                  Game
                  <select
                    value={game}
                    onChange={(e) => {
                      setGame(e.target.value);
                      setMatches(null);
                      setSelected(null);
                      setDetail(null);
                    }}
                  >
                    <option value="mindustry">Mindustry</option>
                    <option value="luanti">Luanti</option>
                  </select>
                </label>
                <label>
                  Player report
                  <textarea
                    autoFocus
                    value={report}
                    onChange={(e) => edit(e.target.value)}
                    rows={7}
                    minLength={10}
                    maxLength={30000}
                    required
                    placeholder="I deleted a data patch and saved my map. When I reopen it, the patch is back…"
                  />
                </label>
                <div className="demo-form-footer">
                  <small>
                    Matching runs in your browser. Your text stays here.
                  </small>
                  <button
                    className="button primary"
                    disabled={!catalog.length || report.trim().length < 10}
                  >
                    <Search size={15} /> Find matching case
                  </button>
                </div>
              </form>
              <div className="demo-examples">
                <span>Or try a player report</span>
                {catalog.map((c) => (
                  <button
                    key={c.id}
                    className="demo-example"
                    onClick={() => {
                      setGame("mindustry");
                      edit(c.sampleReport);
                    }}
                  >
                    <FileText size={14} />
                    {c.title}
                    <ChevronRight size={14} />
                  </button>
                ))}
              </div>
            </section>
            <section className="panel demo-matches" aria-live="polite">
              {matches === null ? (
                <>
                  <div className="eyebrow">
                    A REPORT BECOMES A REVIEWABLE CASE
                  </div>
                  <h2>Follow the evidence.</h2>
                  <p>
                    A report match points to a previous investigation. Review
                    the affected behavior before choosing it.
                  </p>
                  <ol className="demo-preview-steps">
                    <li>
                      <Search size={18} />
                      <div>
                        <strong>Match the behavior</strong>
                        <p>
                          See the affected feature, symptom and missing details.
                        </p>
                      </div>
                    </li>
                    <li>
                      <Play size={18} />
                      <div>
                        <strong>Walk through the investigation</strong>
                        <p>
                          Replay checkpoints, inspect source findings and review
                          the proposed patch.
                        </p>
                      </div>
                    </li>
                    <li>
                      <ShieldCheck size={18} />
                      <div>
                        <strong>See the measured outcome</strong>
                        <p>
                          Passing, blocked and failed candidates retain their
                          actual results.
                        </p>
                      </div>
                    </li>
                  </ol>
                  <div className="demo-library-note">
                    {catalog.length || "…"} recorded cases ·{" "}
                    {catalog.filter((c) => c.allPassed).length} fully validated
                    candidate
                  </div>
                  {detail && (
                    <button
                      className="button secondary"
                      onClick={() => go("reproduce")}
                    >
                      Continue {detail.title}
                      <ArrowRight size={15} />
                    </button>
                  )}
                </>
              ) : matches.length === 0 ? (
                <>
                  <div className="eyebrow">NO RECORDED MATCH</div>
                  <h2>This needs a new investigation.</h2>
                  <p>
                    None of the {catalog.length} bundled cases matches the
                    reported behavior closely enough. Your report has not been
                    reproduced or diagnosed.
                  </p>
                  <button
                    className="button primary"
                    disabled={!connected}
                    onClick={() => onFreshReport(report, game)}
                  >
                    Create investigation from this report
                    <ArrowRight size={15} />
                  </button>
                  {!connected && (
                    <p className="muted">
                      Connect a REPRO backend to create a fresh investigation.
                      You can still try the recorded examples.
                    </p>
                  )}
                </>
              ) : (
                <>
                  <div className="eyebrow">REPORT MAPPING</div>
                  <h2>
                    {matches.length === 1
                      ? "A related investigation"
                      : "Choose the matching behavior"}
                  </h2>
                  <p>
                    Suggested from the feature and symptom in your text. A match
                    is not a new reproduction.
                  </p>
                  {matches.map((match) => (
                    <article className="demo-match-card" key={match.record.id}>
                      <div className="demo-match-label">
                        <span>
                          {match.strength === "strong"
                            ? "Strong report match"
                            : "Possible match · details missing"}
                        </span>
                        <code>#{match.record.issue}</code>
                      </div>
                      <h3>{match.record.title}</h3>
                      <p>{match.record.summary}</p>
                      <ul className="demo-match-reasons">
                        {match.reasons.map((reason) => (
                          <li key={reason}>
                            <Check size={13} />
                            {reason}
                          </li>
                        ))}
                      </ul>
                      {match.missing.length > 0 && (
                        <p className="demo-missing">
                          Check these details: {match.missing.join("; ")}.
                        </p>
                      )}
                      <div className="demo-match-footer">
                        <span
                          className={`demo-outcome ${match.record.allPassed ? "passed" : "blocked"}`}
                        >
                          {match.record.status}
                        </span>
                        <button
                          className="button primary small"
                          onClick={() => choose(match.record.id)}
                        >
                          Review recorded case
                          <ArrowRight size={14} />
                        </button>
                      </div>
                    </article>
                  ))}
                </>
              )}
            </section>
          </div>
        ) : loading ? (
          <div className="loading">
            <LoaderCircle className="spin" />
            Loading the recorded evidence…
          </div>
        ) : detail ? (
          <>
            <div className="demo-case-strip">
              <div>
                <code>{detail.caseId}</code>
                <strong>{detail.title}</strong>
                <small>
                  {detail.modelNote} · recorded {dateTime(detail.recordedAt)}
                </small>
              </div>
              <button
                className="button secondary small"
                onClick={async () => {
                  try {
                    await navigator.clipboard.writeText(window.location.href);
                    setCopied(true);
                  } catch {
                    setError(
                      "Could not copy the link. Copy this page's address to share the selected stage.",
                    );
                  }
                }}
              >
                <Copy size={14} />
                {copied ? "Link copied" : "Copy stage link"}
              </button>
            </div>
            <section className="panel demo-stage-content">
              <div className="demo-stage-heading">
                <div>
                  <span className="eyebrow">
                    {String(index + 1).padStart(2, "0")} /{" "}
                    {demoStages[index].title.toUpperCase()}
                  </span>
                  <h2 ref={heading} tabIndex={-1}>
                    {demoStages[index].description}
                  </h2>
                </div>
                <span className="demo-recorded-tag">Recorded evidence</span>
              </div>
              <DemoStageContent
                detail={detail}
                stage={stage}
                connected={connected}
                freshBody={freshBody}
                onFreshReport={onFreshReport}
                onOpenCase={
                  availableCases.includes(detail.caseId)
                    ? () => onOpenCase(detail.caseId)
                    : undefined
                }
              />
            </section>
            <div className="demo-step-footer">
              <button
                className="button secondary"
                onClick={() => go(demoStages[index - 1].id)}
              >
                <ArrowLeft size={15} />
                {demoStages[index - 1].title}
              </button>
              <small>
                Step {index + 1} of {demoStages.length} · browsing a saved run
              </small>
              {index < demoStages.length - 1 ? (
                <button
                  className="button primary"
                  onClick={() => go(demoStages[index + 1].id)}
                >
                  Continue to {demoStages[index + 1].title.toLowerCase()}
                  <ArrowRight size={15} />
                </button>
              ) : (
                <button
                  className="button secondary"
                  onClick={() => go("report")}
                >
                  Try another report
                  <RotateCcw size={15} />
                </button>
              )}
            </div>
          </>
        ) : null}
      </div>
    </section>
  );
}

function ActionList({ steps }: { steps: DemoAction[] }) {
  return (
    <ol className="demo-action-list">
      {steps.map((step, i) => (
        <li key={i}>
          <code>{String(i + 1).padStart(2, "0")}</code>
          <span>{step.semantic || step.action}</span>
          <small>{step.action}</small>
        </li>
      ))}
    </ol>
  );
}

function FramePlayer({
  frames,
  title,
}: {
  frames: DemoFrame[];
  title: string;
}) {
  const [index, setIndex] = useState(0);
  const [playing, setPlaying] = useState(false);
  const player = useRef<HTMLElement>(null);
  const frame = frames[index];
  useEffect(() => {
    if (!playing) return;
    const timer = setInterval(() => {
      const next = Math.min(index + 1, frames.length - 1);
      setIndex(next);
      if (next === frames.length - 1) setPlaying(false);
    }, 2500);
    return () => clearInterval(timer);
  }, [playing, index, frames.length]);
  return (
    <section ref={player} className="demo-player" aria-label={title}>
      <div className="demo-player-heading">
        <strong>{title}</strong>
        <span>
          Checkpoint {index + 1} / {frames.length}
        </span>
      </div>
      <a
        href={asset(frame.url)}
        target="_blank"
        rel="noreferrer"
        aria-label="Open full recorded screenshot"
      >
        <img
          src={asset(frame.url)}
          alt={frame.label}
          width={1280}
          height={720}
        />
      </a>
      <div className="demo-player-caption">
        <strong>{frame.label}</strong>
        <small>
          {dateTime(frame.recordedAt)} · event {frame.eventSeq}
          {!frame.process.running && " · game process exited"}
        </small>
        {frame.log && (
          <a href={asset(frame.log)} target="_blank" rel="noreferrer">
            Recorded process log
            <ArrowDownToLine size={13} />
          </a>
        )}
      </div>
      <div className="demo-player-controls">
        <button
          className="button secondary small"
          disabled={index === 0}
          onClick={() => {
            setPlaying(false);
            setIndex(index - 1);
          }}
          aria-label="Previous recorded checkpoint"
        >
          <ArrowLeft size={15} />
        </button>
        <button
          className="button secondary small"
          onClick={() => {
            if (index === frames.length - 1) setIndex(0);
            if (!playing)
              player.current?.scrollIntoView({
                behavior: "smooth",
                block: "start",
              });
            setPlaying(!playing);
          }}
        >
          {playing ? <Pause size={14} /> : <Play size={14} />}
          {playing ? "Pause checkpoints" : "Play recorded checkpoints"}
        </button>
        <button
          className="button secondary small"
          disabled={index === frames.length - 1}
          onClick={() => {
            setPlaying(false);
            setIndex(index + 1);
          }}
          aria-label="Next recorded checkpoint"
        >
          <ArrowRight size={15} />
        </button>
        <small>Selected screenshots · 2.5s per checkpoint</small>
      </div>
      <div className="demo-frame-dots">
        {frames.map((f, i) => (
          <button
            key={f.eventSeq}
            aria-label={`Recorded checkpoint ${i + 1}: ${f.label}`}
            aria-current={i === index ? "step" : undefined}
            onClick={() => {
              setPlaying(false);
              setIndex(i);
            }}
          >
            {i + 1}
          </button>
        ))}
      </div>
    </section>
  );
}

function DemoStageContent({
  detail: d,
  stage,
  connected,
  freshBody,
  onFreshReport,
  onOpenCase,
}: {
  detail: DemoDetail;
  stage: DemoStage;
  connected: boolean;
  freshBody: string;
  onFreshReport: (body: string, game: string, commit?: string) => void;
  onOpenCase?: () => void;
}) {
  const r = d.reproduction;
  if (stage === "reproduce")
    return (
      <>
        <p className="demo-lead">{d.summary}</p>
        <div className="demo-stat-row">
          <div>
            <strong>
              {r.successfulRuns}/{r.totalRuns}
            </strong>
            <span>Fresh baseline confirmations</span>
          </div>
          <div>
            <strong>{r.steps.length}</strong>
            <span>Actions in this frozen trigger</span>
          </div>
          <div>
            <strong>{minutes(d.firstReproducedSeconds)}</strong>
            <span>Recorded time to first proof</span>
          </div>
        </div>
        <FramePlayer
          key={`${d.id}-baseline`}
          frames={d.baseline.frames}
          title="Original build · recorded reproduction"
        />
        <div className="demo-evidence-note">
          <strong>Independent verifier</strong>
          <p>{d.baseline.verdict.explanation}</p>
        </div>
        <details className="demo-details">
          <summary>
            Report used for matching and original recorded report
          </summary>
          {freshBody && (
            <>
              <h4>Report used for this walkthrough</h4>
              <p className="demo-preserve-text">{freshBody}</p>
            </>
          )}
          <h4>Original recorded input</h4>
          <pre>{d.report.body}</pre>
        </details>
        <div className="demo-evidence-note">
          <strong>Setup and evidence guidance</strong>
          <p>{d.assistance}</p>
          <p>{d.scope}</p>
        </div>
      </>
    );
  if (stage === "reduce")
    return (
      <>
        <div className="demo-reduction">
          <strong>{r.originalActions}</strong>
          <ArrowRight size={26} />
          <strong>{r.steps.length}</strong>
          <span>recorded trigger actions</span>
        </div>
        <p className="demo-lead">{d.reductionNote}</p>
        <div className="demo-inline-download">
          <span>The exact sequence remains downloadable and inspectable.</span>
          <a
            className="button secondary small"
            href={asset(d.files.replay)}
            download
          >
            <ArrowDownToLine size={14} />
            Download replay
          </a>
        </div>
        <ActionList steps={r.steps} />
      </>
    );
  if (stage === "localize")
    return (
      <>
        <div className="demo-evidence-note">
          <strong>{d.findings.subsystem}</strong>
          <p>{d.findings.root_cause}</p>
        </div>
        <p className="muted">
          These are the recorded AI source findings. The later validation stage
          determines whether the proposed fix actually works.
        </p>
        <div className="demo-source-list">
          {d.findings.candidates.map((candidate, i) => (
            <article key={candidate.path}>
              <span className="demo-source-number">{i + 1}</span>
              <div>
                <a
                  href={`https://github.com/Anuken/Mindustry/blob/${d.targetCommit}/${candidate.path}`}
                  target="_blank"
                  rel="noreferrer"
                >
                  <code>{candidate.path}</code>
                  <Link2 size={14} />
                </a>
                {candidate.symbol && (
                  <p className="muted">{candidate.symbol}</p>
                )}
                <p>{candidate.reasoning}</p>
                <details className="demo-details">
                  <summary>Source evidence</summary>
                  <ul>
                    {candidate.evidence.map((e, j) => (
                      <li key={j}>{e}</li>
                    ))}
                  </ul>
                </details>
              </div>
            </article>
          ))}
        </div>
        <details className="demo-details">
          <summary>Limits of this source analysis</summary>
          <ul>
            {d.findings.limitations.map((limit, i) => (
              <li key={i}>{limit}</li>
            ))}
          </ul>
        </details>
      </>
    );
  if (stage === "patch")
    return (
      <>
        {!d.allPassed && (
          <div className="demo-evidence-note warning">
            <strong>{d.status}</strong>
            <p>
              {d.candidate.successfulRuns === 0
                ? "This proposal did not fix the recorded bug. Its rationale is the model's hypothesis; all five candidate replays still show the symptom."
                : "The recorded gameplay checks pass, but an existing upstream test fails. The candidate is not fully validated."}
            </p>
          </div>
        )}
        <PatchReview
          patch={d.patch}
          error=""
          downloadUrl={asset(d.files.patch)}
          rationale={d.rationale}
          checks={d.checks}
          followupSteps={d.candidate.followups}
        />
      </>
    );
  if (stage === "validate")
    return (
      <>
        <div
          className={`demo-result-banner ${d.allPassed ? "passed" : "blocked"}`}
        >
          <ShieldCheck size={24} />
          <div>
            <strong>{d.allPassed ? "All five checks passed" : d.status}</strong>
            <p>
              {d.allPassed
                ? "The candidate reaches the expected state in five fresh replays. Human review is still pending."
                : d.candidate.successfulRuns === 0
                  ? "The same bug is visible in all five candidate replays, despite a successful build and existing tests."
                  : "The candidate saves and reopens correctly in all five runs. An upstream test's unavailable archive still blocks handoff."}
            </p>
          </div>
        </div>
        <div className="demo-stat-row">
          <div>
            <strong>
              {r.successfulRuns}/{r.totalRuns}
            </strong>
            <span>Baseline bug confirmations</span>
          </div>
          <div>
            <strong>
              {d.candidate.successfulRuns}/{d.candidate.totalRuns}
            </strong>
            <span>Correct candidate outcomes</span>
          </div>
          <div>
            <strong>
              {d.testCounts
                ? `${d.testCounts.tests - d.testCounts.failures - d.testCounts.errors - d.testCounts.skipped}/${d.testCounts.tests}`
                : "Blocked"}
            </strong>
            <span>
              {d.testCounts
                ? `Existing tests · ${d.testCounts.skipped} skips`
                : "Upstream test archive unavailable"}
            </span>
          </div>
        </div>
        <div className="demo-outcome-pair">
          {[
            { label: "Original build", frame: d.baseline.frames.at(-1)! },
            { label: "AI candidate", frame: d.candidate.frames.at(-1)! },
          ].map(({ label, frame }) => (
            <figure key={label}>
              <figcaption>
                <strong>{label}</strong>
                <span>Final recorded checkpoint</span>
              </figcaption>
              <a href={asset(frame.url)} target="_blank" rel="noreferrer">
                <img
                  src={asset(frame.url)}
                  alt={`${label}: ${frame.label}`}
                  width={1280}
                  height={720}
                />
              </a>
              <small>
                {dateTime(frame.recordedAt)} · event {frame.eventSeq}
              </small>
            </figure>
          ))}
        </div>
        <p className="muted">
          {d.candidate.followups.length
            ? `Candidate runs use the unchanged ${r.steps.length}-action trigger plus ${d.candidate.followups.length} frozen save/reopen checks.`
            : `Both versions execute the same ${r.steps.length}-action trigger.`}{" "}
          These images are from selected recorded runs; the counts above cover
          all five repetitions.
        </p>
        <div className="demo-check-table">
          <table>
            <thead>
              <tr>
                <th>Check</th>
                <th>Result</th>
                <th>Recorded evidence</th>
              </tr>
            </thead>
            <tbody>
              {d.checks.map((check) => (
                <tr key={check.name}>
                  <th>{check.name}</th>
                  <td>
                    <span
                      className={`demo-outcome ${check.status === "pass" ? "passed" : "blocked"}`}
                    >
                      {check.status.replaceAll("_", " ").toUpperCase()}
                    </span>
                  </td>
                  <td>
                    {check.detail}
                    {check.artifact && (
                      <a
                        href={asset(check.artifact)}
                        target="_blank"
                        rel="noreferrer"
                      >
                        Open evidence
                        <ArrowDownToLine size={12} />
                      </a>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <details className="demo-details">
          <summary>Inspect all five candidate verdicts</summary>
          {d.candidate.outcomes.map((outcome, i) => (
            <article className="demo-verdict" key={outcome.eventSeq}>
              <strong>
                Run {i + 1} ·{" "}
                {outcome.fixed ? "Correct outcome" : "Fix not established"}
              </strong>
              <small>
                {dateTime(outcome.recordedAt)} · event {outcome.eventSeq}
              </small>
              <p>{outcome.expected.explanation}</p>
            </article>
          ))}
        </details>
        <details className="demo-details">
          <summary>Follow the candidate checkpoints</summary>
          <FramePlayer
            key={`${d.id}-candidate`}
            frames={d.candidate.frames}
            title="Candidate build · recorded validation"
          />
        </details>
      </>
    );
  return (
    <>
      <div
        className={`demo-result-banner ${d.allPassed ? "passed" : "blocked"}`}
      >
        <FileText size={24} />
        <div>
          <strong>
            {d.allPassed ? "Ready for human review" : "Handoff blocked"}
          </strong>
          <p>
            {d.allPassed
              ? "The recorded candidate passes its required checks. Download the report, replay and patch for review."
              : "Keep the failed checks attached to this proposal. Downloading the evidence does not approve the candidate."}
          </p>
        </div>
      </div>
      <div className="demo-downloads">
        <a
          href={asset(d.files.pdf)}
          className="button primary"
          target="_blank"
          rel="noreferrer"
        >
          <FileText size={16} />
          REPRO report · PDF
        </a>
        <a href={asset(d.files.replay)} className="button secondary" download>
          <ArrowDownToLine size={15} />
          Replay YAML
        </a>
        <a href={asset(d.files.patch)} className="button secondary" download>
          <ArrowDownToLine size={15} />
          Candidate patch
        </a>
        <a href={asset(`${d.id}.json`)} className="button secondary" download>
          <ArrowDownToLine size={15} />
          Recording and provenance
        </a>
      </div>
      <div className="demo-handoff-grid">
        <article>
          <h3>The record behind this walkthrough</h3>
          <dl>
            <dt>Case</dt>
            <dd>
              <code>{d.caseId}</code>
            </dd>
            <dt>Target revision</dt>
            <dd>
              <code>{d.targetCommit}</code>
            </dd>
            <dt>Model</dt>
            <dd>{d.modelNote}</dd>
            <dt>Recorded active time</dt>
            <dd>{minutes(d.elapsedSeconds)}</dd>
            <dt>Recorded model calls</dt>
            <dd>{d.usage.model_calls}</dd>
          </dl>
          <p className="muted">
            Browsing this demo makes no model calls. Recorded usage accumulates
            across the original case's jobs.
          </p>
          <a
            className="demo-text-link"
            href={d.files.evidence}
            target="_blank"
            rel="noreferrer"
          >
            Full repository evidence
            <Link2 size={14} />
          </a>
        </article>
        <article>
          <h3>Continue from the report</h3>
          <p>
            A fresh investigation creates a separate case. You can review the
            report and target revision before starting it.
          </p>
          <button
            className="button secondary"
            disabled={!connected}
            onClick={() =>
              onFreshReport(freshBody, "mindustry", d.targetCommit)
            }
          >
            Create a fresh investigation
            <ArrowRight size={15} />
          </button>
          {!connected && (
            <p className="muted">
              A connected REPRO backend is required to run a new investigation.
            </p>
          )}
          {onOpenCase && (
            <button className="button secondary" onClick={onOpenCase}>
              Open the original workspace case
              <ArrowRight size={15} />
            </button>
          )}
        </article>
      </div>
      <details className="demo-details">
        <summary>Recorded stage timestamps and prior attempts</summary>
        <ol className="demo-milestones">
          {d.milestones.map((event) => (
            <li key={event.eventSeq}>
              <time>{dateTime(event.recordedAt)}</time>
              <div>
                <strong>{event.state.replaceAll("_", " ")}</strong>
                <p>{event.summary}</p>
              </div>
            </li>
          ))}
        </ol>
      </details>
      <div className="demo-evidence-note">
        <strong>Evidence scope</strong>
        <p>{d.assistance}</p>
        <p>{d.scope}</p>
        <p>
          No Mindustry patch was published upstream. This walkthrough does not
          submit a handoff approval.
        </p>
      </div>
    </>
  );
}
