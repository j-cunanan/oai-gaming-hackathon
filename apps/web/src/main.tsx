import React, {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import { createRoot } from "react-dom/client";
import {
  Activity,
  AlertTriangle,
  ArrowDownToLine,
  ArrowRight,
  ArrowUpRight,
  Check,
  CheckCheck,
  ChevronRight,
  Clock3,
  Code2,
  Copy,
  Crosshair,
  FileText,
  FlaskConical,
  FolderOpen,
  GitBranch,
  GitPullRequest,
  Layers3,
  LoaderCircle,
  Maximize2,
  Monitor,
  Pause,
  Play,
  Plus,
  RotateCcw,
  Search,
  ShieldCheck,
  Sparkles,
  Terminal,
  X,
} from "lucide-react";
import "./styles.css";
import { HelpTip } from "./help";
import { PatchReview } from "./patch-review";
import { allChecksAccepted, checkAccepted } from "./diff";
import { preferredCase } from "./case-selection";
import { StageActivity, useStageActivity } from "./stage-activity";
import { clockTime, dateTime } from "./activity-model";
import "./case-identity.css";

type CheckResult = {
  name: string;
  status: "pass" | "baseline_failed" | "fail" | "not_run" | "error";
  detail: string;
  artifact: string | null;
  baseline_artifact: string | null;
  failing_tests: string[];
};
type Hypothesis = {
  id: string;
  statement: string;
  prediction: string;
  status: string;
  observation: string;
};
type Candidate = {
  path: string;
  symbol: string | null;
  score: number;
  evidence: string[];
  reasoning: string;
};
type Action = { action: string; semantic: string; [key: string]: unknown };
type Case = {
  imported_from?: {
    source_dir: string;
    imported_at: string;
    original_case_id: string;
  } | null;
  id: string;
  state: string;
  summary: string;
  created_at: string;
  updated_at: string;
  report: {
    title: string;
    body: string;
    game: string;
    target_commit: string;
    platform: string;
    build_version: string | null;
  };
  spec: {
    severity: string;
    bug_class: string;
    known_preconditions: string[];
    uncertain_conditions: string[];
  } | null;
  hypotheses: Hypothesis[];
  latest_screenshot: string | null;
  patch_artifact: string | null;
  patch_rationale: { explanation: string; risks: string[] } | null;
  candidate_verification: { followup_steps: Action[] } | null;
  reproduction: {
    successful_runs: number;
    total_runs: number;
    original_actions: number;
    steps: Action[];
    deterministic: boolean;
  } | null;
  findings: {
    root_cause: string;
    subsystem: string;
    candidates: Candidate[];
    limitations: string[];
  } | null;
  checks: CheckResult[];
  baseline_tests: Record<
    string,
    {
      commit_sha: string;
      timestamp: string;
      status: "running" | "completed" | "error";
      exit_code: number | null;
      failing_tests: string[];
      artifact: string | null;
      detail: string;
    }
  >;
  usage: { model_calls: number; input_tokens: number; output_tokens: number } | null;
  first_reproduced_seconds: number | null;
  elapsed_seconds: number | null;
  benchmark_id: string | null;
};
type Event = {
  seq: number;
  created_at: string;
  kind: string;
  data: Record<string, unknown>;
};
type Artifact = {
  id: string;
  name: string;
  size: number;
  media_type: string;
  sha256: string;
};
type Health = {
  model: string;
  reasoning_effort?: string;
  ai_configured: boolean;
  active_jobs: string[];
  max_model_calls: number;
  repetitions: number;
};
type Benchmark = {
  attempted: number;
  confirmed: number;
  validated_patches: number;
  note: string;
};

const terminal = [
  "COMPLETE",
  "AWAITING_HUMAN",
  "NOT_REPRODUCED",
  "INSUFFICIENT_EVIDENCE",
  "ENVIRONMENT_UNSUPPORTED",
  "FAILED",
  "CANCELLED",
];
const phases = [
  { label: "Triage", states: ["RECEIVED", "TRIAGED"], icon: Search },
  {
    label: "Reproduce",
    states: ["ENVIRONMENT_PREPARING", "READY", "INVESTIGATING", "REPRODUCED"],
    icon: Crosshair,
  },
  { label: "Reduce", states: ["MINIMIZING", "REPRO_CONFIRMED"], icon: Layers3 },
  { label: "Localize", states: ["LOCALIZING", "TEST_GENERATING"], icon: Code2 },
  {
    label: "Validate",
    states: ["PATCH_PROPOSING", "VALIDATING"],
    icon: ShieldCheck,
  },
  {
    label: "Review",
    states: ["AWAITING_HUMAN", "COMPLETE"],
    icon: GitPullRequest,
  },
];
function human(value: string) {
  return value
    .replaceAll("_", " ")
    .toLowerCase()
    .replace(/^./, (x) => x.toUpperCase());
}
function duration(seconds: number | null) {
  if (seconds === null) return "—";
  return `${Math.floor(seconds / 60)}:${String(Math.floor(seconds % 60)).padStart(2, "0")}`;
}
function bytes(n: number) {
  return n > 1024 * 1024
    ? `${(n / 1024 / 1024).toFixed(1)} MB`
    : `${Math.max(1, Math.round(n / 1024))} KB`;
}
function artifactUrl(c: Case, id: string) {
  return `/api/cases/${c.id}/artifacts/${encodeURIComponent(id)}`;
}
async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`/api${path}`, init);
  if (!response.ok) {
    const body = await response
      .json()
      .catch(() => ({ detail: response.statusText }));
    throw new Error(
      typeof body.detail === "string"
        ? body.detail
        : "Check the report fields and exact commit SHA.",
    );
  }
  return response.json();
}
function Badge({ state }: { state: string }) {
  const tone = ["COMPLETE", "REPRO_CONFIRMED"].includes(state)
    ? "green"
    : ["FAILED", "ENVIRONMENT_UNSUPPORTED"].includes(state)
      ? "red"
      : terminal.includes(state)
        ? "amber"
        : "purple";
  return (
    <span className={`badge ${tone}`}>
      <span className="status-dot" />
      {human(state)}
    </span>
  );
}
function RecordingBadge({ c }: { c: Case }) {
  if (!c.imported_from) return null;
  return (
    <span className="recording-badge" title={`Imported from ${c.imported_from.source_dir} at ${dateTime(c.imported_from.imported_at)}`}>
      <strong>Imported recording</strong>
      <small>{c.imported_from.original_case_id} · Recorded {dateTime(c.created_at)}</small>
    </span>
  );
}
function App() {
  const [cases, setCases] = useState<Case[]>([]);
  const [selected, setSelected] = useState("");
  const [current, setCurrent] = useState<Case | null>(null);
  const requestedCase = useRef(
    new URLSearchParams(window.location.search).get("case"),
  );
  const [copiedCase, setCopiedCase] = useState<string | null>(null);
  const [health, setHealth] = useState<Health | null>(null);
  const [stageSelection, setStageSelection] = useState<{
    key: string;
    request: number;
  } | null>(null);
  const activity = useStageActivity(
    current?.id || "",
    current?.updated_at || "",
  );
  const [artifacts, setArtifacts] = useState<Artifact[]>([]);
  const [benchmark, setBenchmark] = useState<Benchmark | null>(null);
  const [page, setPage] = useState("investigations");
  const [tab, setTab] = useState("activity");
  const [showNew, setShowNew] = useState(false);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [connected, setConnected] = useState(false);
  const [patch, setPatch] = useState("");
  const [patchError, setPatchError] = useState("");
  const [filter, setFilter] = useState("");
  const [artifactLimit, setArtifactLimit] = useState(50);
  const [artifactsLoading, setArtifactsLoading] = useState(false);
  const selectedRef = useRef(selected);
  selectedRef.current = selected;
  const refreshTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const eventRevision = useRef(0);
  const filteredArtifacts = useMemo(
    () =>
      artifacts.filter((a) =>
        a.name.toLowerCase().includes(filter.toLowerCase()),
      ),
    [artifacts, filter],
  );

  const refreshList = useCallback(async () => {
    try {
      const [list, status, metrics] = await Promise.all([
        api<Case[]>("/cases"),
        api<Health>("/health"),
        api<Benchmark>("/benchmarks"),
      ]);
      setCases(list);
      setHealth(status);
      setBenchmark(metrics);
      setConnected(true);
      setError((previous) => (previous === "Failed to fetch" ? "" : previous));
      setSelected(
        (id) => id || list.find((c) => c.id === requestedCase.current)?.id || preferredCase(list),
      );
    } catch (e) {
      setConnected(false);
      setError((e as Error).message);
    }
  }, []);
  const refreshCase = useCallback(async () => {
    if (!selected) return;
    try {
      const revision = eventRevision.current;
      const c = await api<Case>(`/cases/${selected}`);
      if (
        selectedRef.current !== selected ||
        revision !== eventRevision.current
      )
        return;
      setCurrent(c);
    } catch (e) {
      setError((e as Error).message);
    }
  }, [selected]);
  const refreshArtifacts = useCallback(async () => {
    if (!selected) return;
    setArtifactsLoading(true);
    try {
      const files = await api<Artifact[]>(`/cases/${selected}/artifacts`);
      if (selectedRef.current === selected) setArtifacts(files);
    } catch (e) {
      if (selectedRef.current === selected) setError((e as Error).message);
    } finally {
      if (selectedRef.current === selected) setArtifactsLoading(false);
    }
  }, [selected]);
  useEffect(() => {
    void refreshList();
    const timer = setInterval(refreshList, 5000);
    return () => clearInterval(timer);
  }, [refreshList]);
  useEffect(() => {
    setCurrent(null);
    setCopiedCase(null);
    setStageSelection(null);
    setArtifacts([]);
    setPatch("");
    setPatchError("");
    setFilter("");
    setArtifactLimit(50);
    eventRevision.current = 0;
    if (!selected) return;
    let disposed = false;
    let source: EventSource | undefined;
    let retry: ReturnType<typeof setTimeout> | undefined;
    async function connect() {
      try {
        const [c, log] = await Promise.all([
          api<Case>(`/cases/${selected}`),
          api<Event[]>(`/cases/${selected}/events?tail=150`),
        ]);
        if (disposed || selectedRef.current !== selected) return;
        setCurrent(c);
        eventRevision.current = log.at(-1)?.seq ?? 0;
        source = new EventSource(
          `/api/cases/${selected}/stream?after=${eventRevision.current}`,
        );
        source.addEventListener("update", (message) => {
          if (disposed || selectedRef.current !== selected) return;
          const e = JSON.parse((message as MessageEvent).data) as Event;
          if (e.seq <= eventRevision.current) return;
          eventRevision.current = e.seq;
          if (e.kind === "action") {
            setCurrent(
              (previous) =>
                previous && {
                  ...previous,
                  latest_screenshot: String(e.data.screenshot_after),
                },
            );
          }
          if (e.kind === "state") void refreshList();
          if (!refreshTimer.current) {
            refreshTimer.current = setTimeout(() => {
              refreshTimer.current = null;
              void refreshCase();
            }, 500);
          }
        });
        source.onerror = () => {
          /* EventSource reconnects with Last-Event-ID; the snapshot poll is a fallback. */
        };
      } catch (e) {
        if (!disposed) {
          setError((e as Error).message);
          retry = setTimeout(connect, 2000);
        }
      }
    }
    void connect();
    const fallback = setInterval(refreshCase, 6000);
    return () => {
      disposed = true;
      source?.close();
      if (retry) clearTimeout(retry);
      clearInterval(fallback);
      if (refreshTimer.current) clearTimeout(refreshTimer.current);
      refreshTimer.current = null;
    };
  }, [selected, refreshCase, refreshList]);
  useEffect(() => {
    if (tab !== "evidence" || !selected) return;
    void refreshArtifacts();
    const timer = setInterval(refreshArtifacts, 5000);
    return () => clearInterval(timer);
  }, [selected, tab, refreshArtifacts]);
  useEffect(() => {
    let disposed = false;
    setPatch("");
    setPatchError("");
    if (current?.patch_artifact)
      fetch(artifactUrl(current, current.patch_artifact))
        .then((r) => {
          if (!r.ok) throw new Error("Could not load the patch.");
          return r.text();
        })
        .then((text) => {
          if (!disposed) setPatch(text);
        })
        .catch(() => {
          if (!disposed)
            setPatchError(
              "Could not load the patch. Reopen this case to retry.",
            );
        });
    return () => {
      disposed = true;
    };
  }, [current?.patch_artifact]);

  async function act(action: string) {
    if (!current) return;
    setBusy(true);
    setError("");
    try {
      await api(`/cases/${current.id}/${action}`, { method: "POST" });
      await refreshCase();
      await refreshList();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  const running = Boolean(current && health?.active_jobs.includes(current.id));
  const viewingCase =
    current?.id === selected ? current : cases.find((c) => c.id === selected);
  useEffect(() => {
    document.title =
      page === "benchmarks"
        ? "REPRO · Benchmark"
        : viewingCase
          ? `${viewingCase.id} · ${viewingCase.report.title} | REPRO`
          : "REPRO · Investigation workspace";
    if (page !== "investigations" || !viewingCase) return;
    const url = new URL(window.location.href);
    if (url.searchParams.get("case") !== viewingCase.id) {
      url.searchParams.set("case", viewingCase.id);
      window.history.replaceState(null, "", url);
    }
  }, [page, viewingCase?.id, viewingCase?.report.title]);
  const confirmed = cases.filter((c) => c.reproduction?.deterministic).length;
  const activePhase = current
    ? phases.findIndex((p) => p.states.includes(current.state))
    : -1;

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <a className="brand" href="#" onClick={() => setPage("investigations")}>
          <span className="brand-mark">
            <Crosshair size={23} strokeWidth={2.6} />
          </span>
          REPRO<span className="beta">LAB</span>
        </a>
        <div className="workspace-label">
          <span className="workspace-avatar">G</span>
          <div>
            Game engineering<small>Local workspace</small>
          </div>
          <ChevronRight size={14} />
        </div>
        <span className="nav-caption">WORKSPACE</span>
        <nav>
          <div className="nav-with-help">
            <button
              className={
                page === "investigations" ? "nav-item selected" : "nav-item"
              }
              onClick={() => setPage("investigations")}
            >
              <Crosshair size={17} />
              Investigations<span className="nav-count">{cases.length}</span>
            </button>
            <HelpTip topic="Investigations" />
          </div>
          <div className="nav-with-help">
            <button
              className={
                page === "benchmarks" ? "nav-item selected" : "nav-item"
              }
              onClick={() => setPage("benchmarks")}
            >
              <FlaskConical size={17} />
              Benchmark
            </button>
            <HelpTip topic="Benchmark" />
          </div>
        </nav>
        <div className="recent-label">
          <span className="nav-caption">RECENT CASES</span>
          <button
            title="New case"
            className="icon-button"
            onClick={() => setShowNew(true)}
          >
            <Plus size={14} />
          </button>
        </div>
        <div className="case-nav">
          {cases.slice(0, 8).map((c) => (
            <button
              key={c.id}
              aria-current={
                selected === c.id && page === "investigations"
                  ? "page"
                  : undefined
              }
              aria-label={`${c.report.title}, case ${c.id}, ${human(c.state)}`}
              className={
                selected === c.id && page === "investigations"
                  ? "case-nav-item chosen"
                  : "case-nav-item"
              }
              onClick={() => {
                setSelected(c.id);
                setPage("investigations");
                setTab("activity");
              }}
            >
              <span
                className={`tiny-dot ${c.reproduction?.deterministic ? "green" : "purple"}`}
              />
              <span className="case-nav-copy">
                <strong>{c.report.title}</strong>
                <code>{c.id}</code>
                <small>{human(c.state)}</small>
                <RecordingBadge c={c} />
              </span>
            </button>
          ))}
          {cases.length === 0 && (
            <p className="muted empty-nav">Your first case starts here.</p>
          )}
        </div>
        <div className="sidebar-bottom">
          <div className="boundary">
            <ShieldCheck size={17} />
            <div>
              Evidence first<small>Every claim needs a replay.</small>
            </div>
          </div>
          <div className="user-avatar">U</div>
          <span>
            Team workspace<small>Hackathon build</small>
          </span>
        </div>
      </aside>
      <div className="main-shell">
        <header className="topbar">
          <div className="breadcrumb">
            <span>Workspace</span>
            <ChevronRight size={13} />
            <strong>
              {page === "benchmarks" ? "Benchmark" : "Investigations"}
            </strong>
            {page === "investigations" && viewingCase && (
              <>
                <ChevronRight size={13} />
                <code
                  className="case-breadcrumb"
                  title={`Viewing case ${viewingCase.id}`}
                >
                  {viewingCase.id}
                </code>
              </>
            )}
          </div>
          <div className="topbar-right">
            <span className="connection">
              <span className={`tiny-dot ${connected ? "green" : "red"}`} />
              {connected ? "Backend connected" : "Backend offline"}
            </span>
            <a
              className="docs-link"
              href="/docs"
              target="_blank"
              rel="noreferrer"
            >
              API docs
              <ArrowUpRight size={13} />
            </a>
          </div>
        </header>
        <main>
          {error && (
            <div role="alert" className="error-banner">
              <span>{error}</span>
              <button
                className="icon-button"
                onClick={() => setError("")}
                aria-label="Dismiss error"
              >
                <X size={16} />
              </button>
            </div>
          )}
          <div className="page-heading">
            <div>
              <div className="eyebrow">
                <span /> AUTONOMOUS BUG OPERATIONS
              </div>
              <h1>
                {page === "benchmarks"
                  ? "Proof, measured."
                  : "From report to reproduction."}
              </h1>
              <p>
                {page === "benchmarks"
                  ? "Historical game bugs. Isolated revisions. Inspectable outcomes."
                  : "Each investigation follows one bug report: reproduce it, diagnose the cause, and review a proposed fix."}
              </p>
            </div>
            <div className="action-with-help">
              <button
                className="button primary"
                onClick={() => setShowNew(true)}
              >
                <Plus size={16} />
                New investigation
              </button>
              <HelpTip topic="New investigation" />
            </div>
          </div>
          {page === "investigations" && viewingCase && (
            <div
              className="selected-case-banner"
              role="status"
              aria-live="polite"
            >
              <div>
                <span className="selected-case-label">
                  VIEWING CASE <HelpTip topic="Case ID" />
                </span>
                <code>{viewingCase.id}</code>
                <strong>{viewingCase.report.title}</strong>
              </div>
              <Badge state={viewingCase.state} />
            </div>
          )}
          <div className="metrics-row">
            <Metric
              label="Total investigations"
              value={String(cases.length).padStart(2, "0")}
              caption="Every attempt retained"
              icon={<FolderOpen size={18} />}
            />
            <Metric
              label="Verified reproductions"
              value={String(confirmed).padStart(2, "0")}
              caption="Includes recorded reproductions"
              icon={<CheckCheck size={18} />}
            />
            <Metric
              label="Worker activity"
              value={health?.active_jobs.length ? "Running" : "Idle"}
              caption={
                health
                  ? `${health.model}${health.reasoning_effort ? ` · ${health.reasoning_effort} reasoning` : ""} · ${health.max_model_calls} calls per job`
                  : "Connecting to backend"
              }
              icon={<Activity size={18} />}
            />
          </div>
          {page === "benchmarks" ? (
            <section className="panel benchmark-panel">
              <div className="panel-title">
                <FlaskConical size={18} />
                <h2>Historical benchmark</h2>
                <span className="tag">MEASURED RUNS</span>
              </div>
              <div className="benchmark-stats">
                <div>
                  <strong>{benchmark?.attempted ?? 0}</strong>
                  <span>
                    Investigation attempts{" "}
                    <HelpTip topic="Investigation attempts" />
                  </span>
                </div>
                <div>
                  <strong>{benchmark?.confirmed ?? 0}</strong>
                  <span>
                    Confirmed replays <HelpTip topic="Confirmed replays" />
                  </span>
                </div>
                <div>
                  <strong>{benchmark?.validated_patches ?? 0}</strong>
                  <span>
                    Validated candidates{" "}
                    <HelpTip topic="Validated candidates" />
                  </span>
                </div>
              </div>
              <p className="benchmark-note">
                {benchmark?.note || "No measurements yet."}
              </p>
              <table>
                <thead>
                  <tr>
                    <th>Case</th>
                    <th>Report</th>
                    <th>Outcome</th>
                    <th>Reproduction</th>
                  </tr>
                </thead>
                <tbody>
                  {cases
                    .filter((c) => c.benchmark_id)
                    .map((c) => (
                      <tr
                        key={c.id}
                        onClick={() => {
                          setSelected(c.id);
                          setPage("investigations");
                        }}
                      >
                        <td>{c.benchmark_id}</td>
                        <td>{c.report.title}</td>
                        <td>
                          <Badge state={c.state} /><RecordingBadge c={c} />
                        </td>
                        <td>
                          {c.reproduction
                            ? `${c.reproduction.successful_runs}/${c.reproduction.total_runs}`
                            : "Not measured"}
                        </td>
                      </tr>
                    ))}
                </tbody>
              </table>
              <div className="integrity-note">
                <ShieldCheck size={18} />
                <p>
                  Future fixes stay outside investigation workspaces. Unit tests
                  and example data never count as benchmark successes.
                </p>
              </div>
            </section>
          ) : cases.length === 0 ? (
            <section className="panel welcome">
              <div className="welcome-art">
                <Crosshair size={55} strokeWidth={1} />
              </div>
              <span className="eyebrow">
                THE INVESTIGATION STARTS WITH A REPORT
              </span>
              <h2>“It crashed somehow.”</h2>
              <p>
                Give REPRO a player report and a historical game revision.
                <br />
                Follow the experiments, then inspect what the evidence supports.
              </p>
              <button
                className="button primary"
                onClick={() => setShowNew(true)}
              >
                Create your first case
                <ArrowRight size={16} />
              </button>
              <div className="welcome-features">
                <span>
                  <Monitor size={15} />
                  Real game control
                </span>
                <span>
                  <RotateCcw size={15} />
                  Repeatable evidence
                </span>
                <span>
                  <GitPullRequest size={15} />
                  Reviewable changes
                </span>
              </div>
            </section>
          ) : (
            <>
              <div className="case-switcher">
                <div className="section-label">
                  INVESTIGATION WORKSPACE{" "}
                  <span>
                    {cases.length} {cases.length === 1 ? "case" : "cases"}
                  </span>
                </div>
                <div className="select-wrap">
                  <select
                    aria-label="Select case"
                    value={selected}
                    onChange={(e) => {
                      setSelected(e.target.value);
                      setTab("activity");
                    }}
                  >
                    {cases.map((c) => (
                      <option key={c.id} value={c.id}>
                        {c.id} · {c.report.title} · {human(c.state)}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
              {!current || current.id !== selected ? (
                <div className="loading">
                  <LoaderCircle className="spin" />
                  Loading case {selected}…
                </div>
              ) : (
                <div className="case-workspace">
                  <div className="case-header">
                    <div className="case-heading-copy">
                      <div className="case-identity">
                        <span>CASE</span>
                        <code>{current.id}</code>
                        <button
                          className="icon-button"
                          title="Copy case ID"
                          aria-label={
                            copiedCase === current.id
                              ? "Case ID copied"
                              : "Copy case ID"
                          }
                          onClick={async () => {
                            try {
                              await navigator.clipboard.writeText(current.id);
                              setCopiedCase(current.id);
                            } catch {
                              setError(
                                "Could not copy the case ID. You can select the visible ID and copy it.",
                              );
                            }
                          }}
                        >
                          {copiedCase === current.id ? (
                            <Check size={13} />
                          ) : (
                            <Copy size={13} />
                          )}
                        </button>
                      </div>
                      <div className="case-meta">
                        <span className="game-name">{current.report.game}</span>
                        {current.benchmark_id && (
                          <span className="benchmark-reference">
                            Benchmark {current.benchmark_id}
                          </span>
                        )}
                        <span className="meta-dot">·</span>
                        <GitBranch size={12} />
                        <code>{current.report.target_commit.slice(0, 8)}</code>
                      </div>
                      <h2>{current.report.title}</h2>
                      <RecordingBadge c={current} />
                    </div>
                    <div className="case-header-actions">
                      <Badge state={current.state} />
                      <HelpTip topic="Case status" />
                      {running ? (
                        <button
                          className="button secondary small"
                          disabled={busy || Boolean(current.imported_from)}
                          onClick={() => act("cancel")}
                        >
                          <Pause size={14} />
                          Stop
                        </button>
                      ) : !current.reproduction ? (
                        <button
                          className="button primary small"
                          disabled={
                            busy ||
                            Boolean(current.imported_from) ||
                            !health?.ai_configured
                          }
                          onClick={() => act("investigate")}
                        >
                          <Play size={14} />
                          Investigate
                        </button>
                      ) : current.reproduction.deterministic &&
                        current.spec &&
                        !current.patch_artifact ? (
                        <button
                          className="button primary small"
                          disabled={
                            busy ||
                            Boolean(current.imported_from) ||
                            !health?.ai_configured
                          }
                          onClick={() => act("continue")}
                        >
                          <Play size={14} />
                          Continue to patch
                        </button>
                      ) : null}
                      <HelpTip
                        topic={
                          running
                            ? "Stop"
                            : !current.reproduction
                              ? "Investigate"
                              : current.reproduction.deterministic &&
                                  current.spec &&
                                  !current.patch_artifact
                                ? "Continue to patch"
                                : ""
                        }
                      />
                    </div>
                  </div>
                  <div className="pipeline">
                    {phases.map((phase, i) => {
                      const Icon = phase.icon;
                      const stageTime = activity.snapshot?.stages.find(
                        (stage) => stage.key === phase.label.toLowerCase(),
                      )?.last_at;
                      const done = activePhase > i;
                      const active = activePhase === i;
                      const failed =
                        phase.label === "Validate" &&
                        (current.checks.some(
                          (check) => !checkAccepted(check),
                        ) ||
                          (done && !allChecksAccepted(current.checks)));
                      const preExisting =
                        phase.label === "Validate" &&
                        !failed &&
                        current.checks.some(
                          (check) => check.status === "baseline_failed",
                        );
                      return (
                        <React.Fragment key={phase.label}>
                          <div
                            className={`phase ${done ? "done" : ""} ${active ? "active" : ""} ${failed ? "failed" : ""} ${preExisting ? "baseline-failed" : ""}`}
                          >
                            <button
                              className="phase-jump"
                              aria-label={`View ${phase.label} activity`}
                              onClick={() => {
                                setTab("activity");
                                setStageSelection((previous) => ({
                                  key: phase.label.toLowerCase(),
                                  request: (previous?.request || 0) + 1,
                                }));
                              }}
                            >
                              <span className="phase-icon">
                                {failed ? (
                                  <X size={13} />
                                ) : preExisting ? (
                                  <AlertTriangle size={13} />
                                ) : done ? (
                                  <Check size={13} />
                                ) : (
                                  <Icon size={14} />
                                )}
                              </span>
                              <span>
                                <span>{failed ? "Checks failed" : preExisting ? "Pre-existing failure" : phase.label}</span>
                                <small
                                  title={
                                    stageTime
                                      ? `Latest recorded: ${dateTime(stageTime)}`
                                      : "No recorded events"
                                  }
                                >
                                  {stageTime ? clockTime(stageTime) : "—"}
                                </small>
                              </span>
                            </button>
                            <HelpTip topic={phase.label} />
                            {active && running && (
                              <span className="phase-pulse" />
                            )}
                          </div>
                          {i < phases.length - 1 && (
                            <span
                              className={`phase-line ${done && !failed ? "done" : ""}`}
                            />
                          )}
                        </React.Fragment>
                      );
                    })}
                  </div>
                  <div className="investigation-grid">
                    <div className="screen-column">
                      <section className="game-screen-panel">
                        <div className="screen-toolbar">
                          <div>
                            <Monitor size={15} />
                            <span>Game viewport</span>
                            <HelpTip topic="Game viewport" />
                            <span
                              className={`live-tag ${running ? "live" : ""}`}
                            >
                              <span />
                              {current.imported_from ? "RECORDED CAPTURE" : running ? "LIVE" : "LAST CAPTURE"}
                            </span>
                          </div>
                          <span>1280 × 720</span>
                          {current.latest_screenshot && (
                            <a
                              title="Open full screenshot"
                              href={artifactUrl(
                                current,
                                current.latest_screenshot,
                              )}
                              target="_blank"
                              rel="noreferrer"
                            >
                              <Maximize2 size={15} />
                            </a>
                          )}
                        </div>
                        <div className="game-viewport">
                          {current.latest_screenshot ? (
                            <img
                              src={artifactUrl(
                                current,
                                current.latest_screenshot,
                              )}
                              alt="Latest recorded game screenshot"
                            />
                          ) : (
                            <div className="viewport-empty">
                              <div className="scan-corners">
                                <Crosshair size={35} strokeWidth={1} />
                              </div>
                              <strong>Waiting for the first frame</strong>
                              <span>
                                The game screen appears when the worker
                                launches.
                              </span>
                            </div>
                          )}
                        </div>
                        <div className="screen-footer">
                          <span>
                            <ShieldCheck size={13} />
                            Isolated Linux desktop
                          </span>
                          <span>Fresh profile on every replay</span>
                        </div>
                      </section>
                      <div className="repro-stats">
                        <div>
                          <span>
                            Reproduction rate{" "}
                            <HelpTip topic="Reproduction rate" />
                          </span>
                          <strong>
                            {current.reproduction ? (
                              <>
                                {current.reproduction.successful_runs}
                                <small>
                                  {" "}
                                  / {current.reproduction.total_runs}
                                </small>
                              </>
                            ) : (
                              "—"
                            )}
                          </strong>
                          <em>
                            {current.reproduction?.deterministic
                              ? "Stable across recorded runs"
                              : "Awaiting confirmation"}
                          </em>
                        </div>
                        <div>
                          <span>
                            Time to first proof{" "}
                            <HelpTip topic="Time to first proof" />
                          </span>
                          <strong>
                            {duration(current.first_reproduced_seconds)}
                          </strong>
                          <em>Measured from investigation start</em>
                        </div>
                        <div>
                          <span>
                            Replay actions <HelpTip topic="Replay actions" />
                          </span>
                          <strong>
                            {current.reproduction ? (
                              <>
                                {current.reproduction.original_actions}
                                <ArrowRight size={17} />
                                {current.reproduction.steps.length}
                              </>
                            ) : (
                              "—"
                            )}
                          </strong>
                          <em>Bounded action reduction</em>
                        </div>
                      </div>
                      <section className="panel report-panel">
                        <div className="panel-title">
                          <FileText size={16} />
                          <h3>Player report</h3>
                          <HelpTip topic="Player report" />
                          {current.spec && (
                            <span className="tag">
                              {current.spec.severity.toUpperCase()}
                              <HelpTip topic="Severity" />
                            </span>
                          )}
                        </div>
                        <p>{current.report.body}</p>
                        <div className="report-tags">
                          <span>{current.report.platform}</span>
                          <span>
                            {current.report.build_version ||
                              "Version unspecified"}
                          </span>
                        </div>
                        {current.spec &&
                          current.spec.uncertain_conditions.length > 0 && (
                            <div className="questions-block">
                              <details>
                                <summary>
                                  Initial questions{" "}
                                  <span>
                                    {current.spec.uncertain_conditions.length}
                                  </span>
                                </summary>
                                <ul>
                                  {current.spec.uncertain_conditions.map(
                                    (q, i) => (
                                      <li key={i}>{q}</li>
                                    ),
                                  )}
                                </ul>
                              </details>
                              <HelpTip topic="Initial questions" />
                            </div>
                          )}
                      </section>
                      {current.reproduction && (
                        <section className="panel replay-panel">
                          <div className="panel-title">
                            <RotateCcw size={16} />
                            <h3>Recorded replay</h3>
                            <HelpTip topic="Recorded replay" />
                            <button
                              className="button secondary small"
                              disabled={busy || running || Boolean(current.imported_from)}
                              onClick={() => act("replay")}
                            >
                              <Play size={12} />
                              Replay bug
                            </button>
                            <HelpTip topic="Replay bug" />
                          </div>
                          <ol>
                            {current.reproduction.steps.map((a, i) => (
                              <li key={i}>
                                <span>{String(i + 1).padStart(2, "0")}</span>
                                <div>
                                  {a.semantic || human(a.action)}
                                  <small>{a.action}</small>
                                </div>
                              </li>
                            ))}
                          </ol>
                          <p className="muted">
                            {current.imported_from ? "Read-only recording. Create a new local case to run another investigation." : "Replay restores the retained pre-patch build."}
                          </p>
                          <button
                            className="button secondary small"
                            disabled={
                              Boolean(current.imported_from) ||
                              busy ||
                              running ||
                              !current.reproduction.deterministic
                            }
                            onClick={() => act("reduce")}
                          >
                            <RotateCcw size={12} />
                            Reduce &amp; revalidate
                          </button>
                          <HelpTip topic="Reduce & revalidate" />
                          <p className="muted">
                            Tests a shorter baseline replay. If it changes,
                            candidate validation runs again.
                          </p>
                        </section>
                      )}
                    </div>
                    <div className="inspector-column">
                      <section className="panel inspector">
                        <div className="inspector-tabs">
                          {[
                            {
                              id: "activity",
                              label: "Activity",
                              icon: Activity,
                            },
                            {
                              id: "evidence",
                              label: "Evidence",
                              icon: Layers3,
                            },
                            { id: "source", label: "Source", icon: Code2 },
                            {
                              id: "patch",
                              label: "Proposed patch",
                              icon: GitPullRequest,
                            },
                          ].map((t) => (
                            <div className="tab-item" key={t.id}>
                              <button
                                className={
                                  tab === t.id
                                    ? "tab-select active"
                                    : "tab-select"
                                }
                                onClick={() => setTab(t.id)}
                              >
                                <t.icon size={14} />
                                {t.label}
                                {t.id === "evidence" &&
                                  artifacts.length > 0 && (
                                    <small>{artifacts.length}</small>
                                  )}
                              </button>
                              <HelpTip topic={t.label} />
                            </div>
                          ))}
                        </div>
                        {tab === "activity" && (
                          <>
                            <div className="activity-status">
                              <span className="activity-orb">
                                <Sparkles size={17} />
                              </span>
                              <div>
                                <strong>
                                  {running
                                    ? "Investigation in progress"
                                    : human(current.state)}
                                </strong>
                                <p>{current.summary}</p>
                              </div>
                              {running && (
                                <LoaderCircle className="spin" size={16} />
                              )}
                            </div>
                            <StageActivity
                              key={current.id}
                              snapshot={activity.snapshot}
                              error={activity.error}
                              retry={activity.retry}
                              selection={stageSelection}
                              checks={current.checks}
                            />
                            <div className="timeline-footer">
                              <Terminal size={13} />
                              <span>
                                {current.usage?.model_calls ?? "—"} model calls
                              </span>
                              <span>
                                {current.usage ? (
                                  current.usage.input_tokens +
                                  current.usage.output_tokens
                                ).toLocaleString() : "—"}{" "}
                                tokens
                              </span>
                              <HelpTip topic="Model usage" />
                            </div>
                          </>
                        )}
                        {tab === "evidence" && (
                          <div className="evidence-tab">
                            <div className="filter-input">
                              <Search size={14} />
                              <input
                                aria-label="Filter artifacts"
                                placeholder="Find an artifact…"
                                value={filter}
                                onChange={(e) => {
                                  setFilter(e.target.value);
                                  setArtifactLimit(50);
                                }}
                              />
                            </div>
                            {filteredArtifacts
                              .slice(0, artifactLimit)
                              .map((a) => (
                                <a
                                  className="artifact-row"
                                  key={a.id}
                                  href={artifactUrl(current, a.id)}
                                  target="_blank"
                                  rel="noreferrer"
                                >
                                  <span className="file-icon">
                                    {a.media_type.startsWith("image") ? (
                                      <Monitor size={16} />
                                    ) : (
                                      <FileText size={16} />
                                    )}
                                  </span>
                                  <span>
                                    <strong>{a.name}</strong>
                                    <small>
                                      {bytes(a.size)} · SHA-256{" "}
                                      {a.sha256.slice(0, 10)}
                                    </small>
                                  </span>
                                  <ArrowUpRight size={14} />
                                </a>
                              ))}
                            {filteredArtifacts.length > artifactLimit && (
                              <button
                                className="button secondary small"
                                onClick={() =>
                                  setArtifactLimit((count) => count + 50)
                                }
                              >
                                Show 50 more (
                                {filteredArtifacts.length - artifactLimit}{" "}
                                remaining)
                              </button>
                            )}
                            {artifactsLoading && artifacts.length === 0 && (
                              <p className="muted">Loading evidence…</p>
                            )}
                            {!artifactsLoading && artifacts.length === 0 && (
                              <EmptyPanel
                                icon={<Layers3 />}
                                text="Screenshots, logs and replay files appear after an experiment."
                              />
                            )}
                          </div>
                        )}
                        {tab === "source" && (
                          <div className="source-tab">
                            {current.findings ? (
                              <>
                                <span className="eyebrow">
                                  {current.findings.subsystem}
                                </span>
                                <h3>Evidence-backed localization</h3>
                                <p>{current.findings.root_cause}</p>
                                {current.findings.candidates.map((c, i) => (
                                  <div
                                    className="source-candidate"
                                    key={c.path}
                                  >
                                    <div>
                                      <span className="rank">{i + 1}</span>
                                      <code>{c.path}</code>
                                      <span className="source-score">
                                        {c.score.toFixed(2)}
                                        <HelpTip topic="Source score" />
                                      </span>
                                    </div>
                                    <strong>{c.symbol}</strong>
                                    <p>{c.reasoning}</p>
                                    <details>
                                      <summary>Supporting evidence</summary>
                                      <ul>
                                        {c.evidence.map((e, i) => (
                                          <li key={i}>{e}</li>
                                        ))}
                                      </ul>
                                    </details>
                                  </div>
                                ))}
                              </>
                            ) : (
                              <EmptyPanel
                                icon={<Code2 />}
                                text="Source investigation follows a confirmed reproduction."
                              />
                            )}
                          </div>
                        )}
                        {tab === "patch" && (
                          <PatchReview
                            patch={patch}
                            error={patchError}
                            downloadUrl={
                              current.patch_artifact
                                ? artifactUrl(current, current.patch_artifact)
                                : null
                            }
                            rationale={current.patch_rationale ?? null}
                            followupSteps={current.candidate_verification?.followup_steps}
                            checks={current.checks}
                          />
                        )}
                      </section>
                      <section className="panel hypothesis-panel">
                        <div className="panel-title">
                          <FlaskConical size={16} />
                          <h3>Hypotheses</h3>
                          <HelpTip topic="Hypotheses" />
                          <span className="muted">
                            {current.hypotheses.length}
                          </span>
                        </div>
                        {current.hypotheses.length ? (
                          current.hypotheses.map((h) => (
                            <div className="hypothesis" key={h.id}>
                              <span className={`hypothesis-status ${h.status}`}>
                                <FlaskConical size={13} />
                              </span>
                              <div>
                                <span className="hypothesis-id">
                                  {h.id} <span>{human(h.status)}</span>
                                </span>
                                <p>{h.statement}</p>
                                {h.observation && (
                                  <small>{h.observation}</small>
                                )}
                              </div>
                            </div>
                          ))
                        ) : (
                          <div className="small-empty">
                            Testable explanations will be recorded here.
                          </div>
                        )}
                      </section>
                      {current.checks.length > 0 && (
                        <section className="panel validation-panel">
                          <div className="panel-title">
                            <ShieldCheck size={16} />
                            <h3>Validation gates</h3>
                            <HelpTip topic="Validation gates" />
                            <button
                              className="icon-button"
                              title="Rerun validation"
                              disabled={running || busy || Boolean(current.imported_from)}
                              onClick={() => act("validate")}
                            >
                              <RotateCcw size={14} />
                            </button>
                            <HelpTip topic="Rerun validation" />
                          </div>
                          {current.checks.map((c) => (
                            <div className="validation-row" key={c.name}>
                              <span className={`check-icon ${c.status}`}>
                                {c.status === "pass" ? (
                                  <Check size={13} />
                                ) : c.status === "baseline_failed" ? (
                                  <AlertTriangle size={13} />
                                ) : c.status === "fail" ? (
                                  <X size={13} />
                                ) : (
                                  <Clock3 size={13} />
                                )}
                              </span>
                              <div>
                                <strong>
                                  {c.name} <HelpTip topic={c.name} />
                                </strong>
                                {c.status === "baseline_failed" && (
                                  <p className="baseline-notice">
                                    Pre-existing — fails on baseline too
                                  </p>
                                )}
                                <p>{c.detail}</p>
                                {c.name === "Existing tests" &&
                                  current.baseline_tests?.[
                                    current.report.target_commit
                                  ] && (
                                    <p>
                                      Baseline{" "}
                                      {current.report.target_commit.slice(0, 8)}{" "}
                                      ·{" "}
                                      {
                                        current.baseline_tests[
                                          current.report.target_commit
                                        ].timestamp
                                      }
                                      {" · "}
                                      {
                                        current.baseline_tests[
                                          current.report.target_commit
                                        ].status
                                      }
                                      {" · exit "}
                                      {current.baseline_tests[
                                        current.report.target_commit
                                      ].exit_code ?? "unavailable"}
                                    </p>
                                  )}
                                <div className="validation-logs">
                                  {c.baseline_artifact && (
                                    <a
                                      href={artifactUrl(
                                        current,
                                        c.baseline_artifact,
                                      )}
                                      target="_blank"
                                      rel="noreferrer"
                                    >
                                      Baseline log
                                    </a>
                                  )}
                                  {c.artifact && (
                                    <a
                                      href={artifactUrl(current, c.artifact)}
                                      target="_blank"
                                      rel="noreferrer"
                                    >
                                      {c.name === "Existing tests"
                                        ? "Candidate log"
                                        : "Evidence"}
                                    </a>
                                  )}
                                </div>
                              </div>
                              <span className={`check-label ${c.status}`}>
                                {c.status === "baseline_failed"
                                  ? "pre-existing"
                                  : c.status.replace("_", " ")}
                              </span>
                            </div>
                          ))}
                        </section>
                      )}
                    </div>
                  </div>
                  <footer className="case-footer">
                    <span>
                      <ShieldCheck size={15} />
                      Conclusions stay tied to recorded evidence.
                    </span>
                    <div>
                      <div className="action-with-help">
                        <a
                          className="button secondary small"
                          href={`/api/cases/${current.id}/report`}
                          download={`repro-report-${current.id}.pdf`}
                        >
                          <ArrowDownToLine size={14} />
                          Export PDF
                        </a>
                        <HelpTip topic="Export PDF" />
                      </div>
                      {current.state === "AWAITING_HUMAN" && (
                        <>
                          <div className="action-with-help">
                            <button
                              className="button secondary small"
                              disabled={busy || running || Boolean(current.imported_from)}
                              onClick={() => act("reject")}
                            >
                              Reject patch
                            </button>
                            <HelpTip topic="Reject patch" />
                          </div>
                          <div className="action-with-help">
                            <button
                              className="button primary small"
                              disabled={
                              Boolean(current.imported_from) ||
                                busy ||
                                running ||
                                !current.patch_artifact ||
                                !allChecksAccepted(current.checks) ||
                                current.checks.some((c) => !checkAccepted(c))
                              }
                              onClick={() => act("approve")}
                            >
                              <Check size={14} />
                              Approve for handoff
                            </button>
                            <HelpTip topic="Approve for handoff" />
                          </div>
                        </>
                      )}
                    </div>
                  </footer>
                </div>
              )}
            </>
          )}
          <div className="page-footer">
            <span>REPRO / BUILT FOR GAME ENGINEERS</span>
            <span>Observe. Experiment. Verify.</span>
          </div>
        </main>
      </div>
      {showNew && (
        <NewCase
          onClose={() => setShowNew(false)}
          onCreated={(c) => {
            setSelected(c.id);
            setPage("investigations");
            setShowNew(false);
            void refreshList();
          }}
        />
      )}
    </div>
  );
}
function Metric({
  label,
  value,
  caption,
  icon,
}: {
  label: string;
  value: string;
  caption: string;
  icon: React.ReactNode;
}) {
  return (
    <div className="metric">
      <div>
        <span>
          {label} <HelpTip topic={label} />
        </span>
        {icon}
      </div>
      <strong>{value}</strong>
      <p>{caption}</p>
    </div>
  );
}
function EmptyPanel({ icon, text }: { icon: React.ReactNode; text: string }) {
  return (
    <div className="inspector-empty">
      {icon}
      <p>{text}</p>
    </div>
  );
}
function NewCase({
  onClose,
  onCreated,
}: {
  onClose: () => void;
  onCreated: (c: Case) => void;
}) {
  const [title, setTitle] = useState("");
  const [body, setBody] = useState("");
  const [commit, setCommit] = useState("");
  const [game, setGame] = useState("mindustry");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  useEffect(() => {
    const escape = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", escape);
    return () => window.removeEventListener("keydown", escape);
  }, [onClose]);
  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setError("");
    try {
      const c = await api<Case>("/cases", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          title,
          body,
          game,
          target_commit: commit,
          platform: "Linux",
        }),
      });
      onCreated(c);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setSaving(false);
    }
  }
  return (
    <div className="modal-overlay">
      <section
        className="modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="new-title"
      >
        <div className="modal-heading">
          <span className="modal-icon">
            <Crosshair size={22} />
          </span>
          <button
            className="icon-button"
            aria-label="Close new investigation"
            onClick={onClose}
          >
            <X size={19} />
          </button>
        </div>
        <div className="eyebrow">START WITH THE PLAYER'S EVIDENCE</div>
        <h2 id="new-title">New investigation</h2>
        <p>Pin a game revision and describe what went wrong.</p>
        <form onSubmit={submit}>
          <label>
            Report title
            <input
              autoFocus
              required
              minLength={3}
              maxLength={250}
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g. The game crashes when I open my save"
            />
          </label>
          <label>
            Player report
            <textarea
              required
              minLength={10}
              maxLength={30000}
              rows={5}
              value={body}
              onChange={(e) => setBody(e.target.value)}
              placeholder="Paste the report, observed behavior and any reproduction hints. Keep uncertainties intact."
            />
          </label>
          <div className="form-row">
            <label>
              Game
              <select value={game} onChange={(e) => setGame(e.target.value)}>
                <option value="mindustry">Mindustry</option>
                <option value="luanti">Luanti (experimental)</option>
              </select>
            </label>
            <label>
              Exact target commit
              <input
                required
                pattern="[0-9a-f]{40}"
                title="Full 40-character Git commit SHA"
                value={commit}
                onChange={(e) => setCommit(e.target.value.trim())}
                placeholder="40-character SHA"
              />
            </label>
          </div>
          <div className="form-note">
            <GitBranch size={14} />
            <span>
              {game === "mindustry"
                ? "Anuken / Mindustry"
                : "luanti-org / luanti"}{" "}
              · isolated historical checkout
            </span>
          </div>
          {error && (
            <div role="alert" className="error-banner">
              {error}
            </div>
          )}
          <div className="modal-footer">
            <button
              type="button"
              className="button secondary"
              onClick={onClose}
            >
              Cancel
            </button>
            <button className="button primary" disabled={saving}>
              {saving ? (
                <LoaderCircle className="spin" size={15} />
              ) : (
                <Plus size={15} />
              )}
              Create case
            </button>
          </div>
        </form>
      </section>
    </div>
  );
}

createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
