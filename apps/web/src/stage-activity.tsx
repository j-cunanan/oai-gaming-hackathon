import { useEffect, useRef, useState } from "react";
import {
  ChevronDown,
  ChevronRight,
  Download,
  FileText,
  Search,
} from "lucide-react";
import { HelpTip } from "./help";
import {
  clockTime,
  dateTime,
  filterActivity,
  mergeActivity,
} from "./activity-model";
import type { ActivityEntry, ActivitySnapshot } from "./activity-model";
import "./stage-activity.css";

export function useStageActivity(caseId: string, version: string) {
  const [snapshot, setSnapshot] = useState<ActivitySnapshot | null>(null);
  const [error, setError] = useState("");
  const [attempt, setAttempt] = useState(0);
  const cursor = useRef({ caseId: "", seq: 0 });
  useEffect(() => {
    if (cursor.current.caseId !== caseId) {
      cursor.current = { caseId, seq: 0 };
      setSnapshot(null);
      setError("");
    }
    if (!caseId) return;
    const controller = new AbortController();
    fetch(`/api/cases/${caseId}/activity?after=${cursor.current.seq}`, {
      signal: controller.signal,
    })
      .then((response) => {
        if (!response.ok) throw new Error("Could not load stage activity.");
        return response.json() as Promise<ActivitySnapshot>;
      })
      .then((data) => {
        if (controller.signal.aborted || cursor.current.caseId !== caseId)
          return;
        cursor.current.seq = data.last_seq;
        setSnapshot((previous) => mergeActivity(previous, data));
        setError("");
      })
      .catch((error) => {
        if (!controller.signal.aborted) setError(error.message);
      });
    return () => controller.abort();
  }, [caseId, version, attempt]);
  return {
    snapshot: snapshot?.case_id === caseId ? snapshot : null,
    error,
    retry: () => setAttempt((value) => value + 1),
  };
}

function EventRow({ event, caseId }: { event: ActivityEntry; caseId: string }) {
  const [expanded, setExpanded] = useState(false);
  const [record, setRecord] = useState("");
  const [error, setError] = useState("");
  useEffect(() => {
    if (!expanded || record) return;
    const controller = new AbortController();
    setError("");
    fetch(`/api/cases/${caseId}/events/${event.seq}`, {
      signal: controller.signal,
    })
      .then((response) => {
        if (!response.ok)
          throw new Error("Record unavailable. Close and reopen to retry.");
        return response.json();
      })
      .then((data) => {
        if (!controller.signal.aborted)
          setRecord(JSON.stringify(data.data, null, 2));
      })
      .catch((error) => {
        if (!controller.signal.aborted) setError(error.message);
      });
    return () => controller.abort();
  }, [expanded, caseId, event.seq, record]);
  return (
    <article
      className={`stage-event ${event.attention ? "needs-attention" : ""}`}
    >
      <time
        dateTime={event.created_at}
        title={new Date(event.created_at).toISOString()}
      >
        {clockTime(event.created_at)}
      </time>
      <div className="stage-event-content">
        <span className="stage-event-kind">
          {event.kind.replaceAll("_", " ")}
          {event.attention && <b>Needs attention</b>}
        </span>
        <p>{event.summary}</p>
        <div className="stage-event-links">
          {event.artifacts.map((link) => (
            <a
              key={link.id}
              href={`/api/cases/${caseId}/artifacts/${encodeURIComponent(link.id)}`}
              target="_blank"
              rel="noreferrer"
            >
              <FileText size={12} />
              {link.label}
            </a>
          ))}
          <button
            onClick={() => setExpanded((value) => !value)}
            aria-expanded={expanded}
            aria-label={`${expanded ? "Hide" : "View"} record ${event.seq}`}
          >
            {expanded ? "Hide details" : "View details"}
          </button>
        </div>
        {expanded && (
          <pre className="stage-event-record">
            {error || record || "Loading record…"}
          </pre>
        )}
      </div>
    </article>
  );
}

export function StageActivity({
  snapshot,
  error,
  retry,
  selection,
  checks,
}: {
  snapshot: ActivitySnapshot | null;
  error: string;
  retry: () => void;
  selection: { key: string; request: number } | null;
  checks: { name: string; status: string; artifact: string | null }[];
}) {
  const [openStage, setOpenStage] = useState("validate");
  const [query, setQuery] = useState("");
  const [closedMatches, setClosedMatches] = useState<Record<string, boolean>>(
    {},
  );
  const [includeModel, setIncludeModel] = useState(false);
  const [newestFirst, setNewestFirst] = useState(true);
  const [limits, setLimits] = useState<Record<string, number>>({});
  const stageRefs = useRef<Record<string, HTMLButtonElement | null>>({});
  const initialized = useRef(false);
  useEffect(() => {
    if (!snapshot || initialized.current) return;
    initialized.current = true;
    const latest = [...snapshot.events]
      .reverse()
      .find((event) => event.stage !== "review");
    setOpenStage(selection?.key || latest?.stage || "triage");
  }, [snapshot, selection]);
  useEffect(() => {
    if (!selection) return;
    setQuery("");
    setOpenStage(selection.key);
    const frame = requestAnimationFrame(() => {
      stageRefs.current[selection.key]?.scrollIntoView({
        behavior: "smooth",
        block: "start",
      });
      stageRefs.current[selection.key]?.focus({ preventScroll: true });
    });
    return () => cancelAnimationFrame(frame);
  }, [selection]);
  if (!snapshot)
    return (
      <div className="small-empty" role={error ? "alert" : undefined}>
        {error || "Loading stage history…"}
        {error && (
          <button className="button secondary small" onClick={retry}>
            Retry
          </button>
        )}
      </div>
    );
  const matches = filterActivity(snapshot.events, query, includeModel);
  const zone = Intl.DateTimeFormat().resolvedOptions().timeZone;
  return (
    <div className="stage-activity">
      <div className="stage-activity-heading">
        <div>
          <strong>Activity by stage</strong>
          <HelpTip topic="Stage timestamps" />
          <p>Clock times in {zone}. Open a stage to inspect its log.</p>
        </div>
        <a
          href={`/api/cases/${snapshot.case_id}/activity`}
          download={`repro-activity-${snapshot.case_id}.json`}
          aria-label="Download full activity log"
          title="Download full activity log"
        >
          <Download size={16} />
        </a>
      </div>
      {error && (
        <div className="stage-load-error" role="alert">
          {error} Showing the last saved entries.{" "}
          <button onClick={retry}>Retry</button>
        </div>
      )}
      <div className="stage-search">
        <Search size={14} />
        <input
          aria-label="Search stage activity"
          placeholder="Search all stages…"
          value={query}
          onChange={(event) => {
            setQuery(event.target.value);
            setClosedMatches({});
            setLimits({});
          }}
        />
      </div>
      <div className="stage-log-options">
        <label>
          <input
            type="checkbox"
            checked={includeModel}
            onChange={(event) => {
              setIncludeModel(event.target.checked);
              setLimits({});
            }}
          />
          Include model calls & observations
        </label>
        <button onClick={() => setNewestFirst((value) => !value)}>
          {newestFirst ? "Newest first" : "Oldest first"}
        </button>
      </div>
      {query && matches.length === 0 && (
        <p className="small-empty">
          No matching entries. Try another phrase or include model calls.
        </p>
      )}
      {snapshot.stages.map((stage) => {
        const events = matches.filter((event) => event.stage === stage.key);
        if (query && !events.length) return null;
        const expanded = query
          ? !closedMatches[stage.key]
          : openStage === stage.key;
        const ordered = newestFirst ? [...events].reverse() : events;
        const visible = ordered.slice(0, limits[stage.key] || 40);
        return (
          <section
            className={`stage-group ${expanded ? "expanded" : ""}`}
            key={stage.key}
          >
            <button
              className="stage-group-toggle"
              ref={(node) => {
                stageRefs.current[stage.key] = node;
              }}
              aria-expanded={expanded}
              aria-controls={`stage-log-${stage.key}`}
              onClick={() => {
                if (query)
                  setClosedMatches((previous) => ({
                    ...previous,
                    [stage.key]: expanded,
                  }));
                else setOpenStage(expanded ? "" : stage.key);
              }}
            >
              <span className="stage-group-name">
                {expanded ? (
                  <ChevronDown size={15} />
                ) : (
                  <ChevronRight size={15} />
                )}
                <strong>{stage.label}</strong>
                <span>{events.length} entries</span>
              </span>
              <span className="stage-group-times">
                {stage.first_at ? (
                  <>
                    <span>
                      First entry{" "}
                      <time dateTime={stage.first_at}>
                        {dateTime(stage.first_at)}
                      </time>
                    </span>
                    <span>
                      Latest{" "}
                      <time dateTime={stage.last_at!}>
                        {dateTime(stage.last_at!)}
                      </time>
                    </span>
                  </>
                ) : (
                  "No recorded events yet"
                )}
              </span>
            </button>
            {expanded && (
              <div id={`stage-log-${stage.key}`} className="stage-group-log">
                {stage.key === "validate" &&
                  checks.some((check) => check.artifact) && (
                    <div className="stage-check-links">
                      <span>Latest validation logs</span>
                      {checks
                        .filter((check) => check.artifact)
                        .map((check) => (
                          <a
                            key={check.name}
                            href={`/api/cases/${snapshot.case_id}/artifacts/${encodeURIComponent(check.artifact!)}`}
                            target="_blank"
                            rel="noreferrer"
                          >
                            <FileText size={12} />
                            {check.name}
                            <b className={check.status}>
                              {check.status.replaceAll("_", " ")}
                            </b>
                          </a>
                        ))}
                    </div>
                  )}
                {!visible.length && (
                  <p className="small-empty">
                    {stage.event_count
                      ? "Only model calls or observations are recorded. Enable them above to view."
                      : "This stage has no recorded activity yet."}
                  </p>
                )}
                {visible.map((event, index) => (
                  <DatedEvent
                    key={event.seq}
                    event={event}
                    caseId={snapshot.case_id}
                    previous={visible[index - 1]}
                  />
                ))}
                {ordered.length > visible.length && (
                  <button
                    className="stage-load-more"
                    onClick={() =>
                      setLimits((previous) => ({
                        ...previous,
                        [stage.key]: visible.length + 40,
                      }))
                    }
                  >
                    Show 40 more · {ordered.length - visible.length} remaining
                  </button>
                )}
              </div>
            )}
          </section>
        );
      })}
    </div>
  );
}

function DatedEvent({
  event,
  previous,
  caseId,
}: {
  event: ActivityEntry;
  previous?: ActivityEntry;
  caseId: string;
}) {
  const date = new Date(event.created_at).toLocaleDateString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
  const priorDate =
    previous &&
    new Date(previous.created_at).toLocaleDateString(undefined, {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  return (
    <>
      {date !== priorDate && <div className="stage-date-divider">{date}</div>}
      <EventRow event={event} caseId={caseId} />
    </>
  );
}
