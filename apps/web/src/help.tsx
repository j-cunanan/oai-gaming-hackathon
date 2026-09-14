import { useEffect, useId, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { Info } from "lucide-react";

const explanations: Record<string, string> = {
  "Case ID":
    "The unique ID for this investigation. Reports can have the same title and benchmark label, but each case has its own ID, history, and results. The selected ID appears in the header, browser tab, and URL; reloading keeps that case selected.",
  Investigations:
    "An investigation is one bug case: a player report, attempts to reproduce it, evidence, a source diagnosis, and any proposed patch. A case can finish without finding a fix.",
  "New investigation":
    "Create a separate bug case from a player report and an exact game revision. Starting it launches the game worker and uses the configured AI model.",
  "Total investigations":
    "The number of saved bug cases, including unsuccessful and unfinished cases. Rerunning a case does not create a new investigation.",
  "Verified reproductions":
    "Cases where the reported symptom appeared in every required fresh baseline replay. This confirms a reproduction, not a completed fix.",
  "Worker activity":
    "Running means a job is running or queued. Jobs share one local worker slot. The model-call limit applies to each job; case usage accumulates across jobs.",
  Benchmark:
    "Recorded attempts on selected historical bug reports. These counts describe this workspace and do not measure general accuracy.",
  "Investigation attempts":
    "Saved investigations linked to a historical benchmark case. Several investigations can evaluate the same underlying bug.",
  "Confirmed replays":
    "Benchmark investigations with a confirmed, repeatable baseline reproduction.",
  "Validated candidates":
    "Proposed patches whose five required validation checks passed or whose existing-test failures match recorded baseline evidence. Human approval is tracked separately.",
  Triage:
    "Turn the player report into a bug description, expected behavior, known conditions, and open questions.",
  Reproduce:
    "Launch the original game and try to observe the reported symptom, then repeat the recorded actions from fresh profiles.",
  Reduce:
    "Try removing unnecessary recorded actions while retaining the bug. A shorter replay must pass fresh confirmations.",
  Localize:
    "Inspect the original source and rank the files or functions that best explain the reproduced behavior.",
  Validate:
    "Check the original reproduction, candidate build, existing tests, replay after the patch, and a clean startup. Every required check must pass before approval.",
  Review:
    "Inspect the proposed patch, its explanation, risks, and validation evidence. Approval records a local handoff decision.",
  "Case status":
    "The latest saved outcome or stage. Awaiting human means a patch needs review; its checks determine whether approval is available. Insufficient evidence means a reliable reproduction was not established. Failed means the job encountered an error.",
  "Game viewport":
    "The latest saved screenshot from the isolated game desktop. LIVE updates after captured actions; it is not a continuous video stream.",
  "Reproduction rate":
    "Successful baseline replays divided by completed baseline replays in the current confirmation set. For example, 5/5 means the original bug appeared in all five fresh runs.",
  "Time to first proof":
    "Elapsed investigation time before the reported symptom was first independently verified. Preparation is excluded; this is not total time to a fix.",
  "Replay actions":
    "The original number of recorded actions followed by the current reduced count. Clicks, key presses, typing, scrolling, and waits all count.",
  "Player report":
    "The original bug description supplied to this case. The investigation's findings and proposed patch are recorded separately.",
  Severity:
    "The AI's triage estimate from the report. Unknown means there was not enough information to judge impact; it does not mean harmless.",
  "Initial questions":
    "Questions recorded before the investigation. Later findings and validation may address them; they are retained to show what was uncertain at intake.",
  "Recorded replay":
    "The saved action sequence used to test the symptom. The reproduction rate shows whether it was stable across fresh runs.",
  "Replay bug":
    "Run the saved actions once on the retained original build with a fresh profile and verify the symptom. This uses the worker and may use an AI verification call.",
  "Reduce & revalidate":
    "Try a shorter baseline replay. If the sequence changes, confirm it again and rerun candidate validation. This uses worker time and AI calls.",
  Investigate:
    "Start the AI investigation for this case. It launches the game, records experiments, and continues toward source diagnosis and a proposed patch when evidence supports it.",
  Stop: "Cancel the active or queued job for this case. Completed events, screenshots, and partial results remain saved.",
  Activity:
    "The full recorded history grouped by investigation stage. Search across stages, include model calls, and open screenshots, game logs, or event details. Entries are loaded incrementally as the investigation runs.",
  Evidence:
    "Saved screenshots, logs, reports, replays, and patch files. A SHA-256 value identifies the exact file contents. Search covers the full artifact index.",
  Source:
    "The source diagnosis and ranked files/functions. A source match helps explain a bug but does not by itself prove the game reproduced it.",
  "Source score":
    "The investigator's 0-to-1 relevance score for this file. It is a ranking signal, not a calibrated probability that the fix is correct.",
  "Proposed patch":
    "The candidate diff is the proposed patch: exact source lines to add or remove. It is applied in the disposable game workspace for testing and awaits review before handoff.",
  "Why this patch should work":
    "The explanation saved when this exact patch was proposed. The validation results show what was subsequently tested; the explanation alone is not proof.",
  Changes:
    "Green + lines are added, red - lines are removed, and neutral lines provide context. Old and New are line numbers before and after the patch. The download preserves the exact patch file.",
  Hypotheses:
    "Testable explanations considered by the investigator. Supported means recorded observations support the idea; it is not a guarantee that every related bug is fixed.",
  "Validation gates":
    "Five required checks protect the handoff decision. A failure, error, or check that did not run keeps approval unavailable.",
  "Regression before patch":
    "Verify that the saved trigger still reproduces the bug on the retained original build, before judging the proposed fix.",
  "Candidate build":
    "Compile the game with the proposed patch. Passing proves the build command succeeded, not that the bug is fixed.",
  "Existing tests":
    "Run the game's existing automated tests. Inspect the log for details; a failed test keeps approval blocked.",
  "Original replay after patch":
    "Run the same recorded actions on the patched game. The required target screen/state must be reached and the original symptom must be absent on every run.",
  "Smoke test":
    "A separate clean launch checks that the patched game starts and stays running through startup. It is not broad gameplay coverage.",
  "Rerun validation":
    "Recheck the baseline and candidate using the current worker. Earlier results are preserved. This runs builds, tests, fresh replays, and AI verification calls.",
  "Export PDF":
    "Download a plain REPRO Report with the saved diagnosis, patch explanation, risks, checks, and screenshots. Export makes no AI calls.",
  "Reject patch":
    "Record that you do not accept this proposed patch. The evidence remains saved and no upstream change is published.",
  "Approve for handoff":
    "Available only when all required checks are satisfied, including recorded pre-existing test failures, and the case is idle. Records your approval locally; a reviewed upstream pull request is still a separate step.",
  "Stage timestamps":
    "First entry and Latest are exact saved event times, shown in your local time zone. They include repeated attempts and pauses, so the interval is not active work duration. Stage buttons show the latest event time and open that stage’s log. PDF timestamps use UTC.",
  "Model usage":
    "Calls and input/output tokens used across this case's jobs. These are measured usage counts, not a dollar estimate. Viewing or exporting saved evidence makes no model calls.",
};

export function HelpTip({ topic }: { topic: string }) {
  const id = useId();
  const trigger = useRef<HTMLButtonElement>(null);
  const bubble = useRef<HTMLDivElement>(null);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const [position, setPosition] = useState<{
    left: number;
    top?: number;
    bottom?: number;
  } | null>(null);
  const text = explanations[topic];
  function hide() {
    setPosition(null);
  }
  function show() {
    if (timer.current) clearTimeout(timer.current);
    const rect = trigger.current?.getBoundingClientRect();
    if (!rect) return;
    const width = Math.min(280, window.innerWidth - 24);
    setPosition({
      left: Math.max(
        12,
        Math.min(rect.left - 12, window.innerWidth - width - 12),
      ),
      ...(rect.bottom + 180 > window.innerHeight
        ? { bottom: window.innerHeight - rect.top + 8 }
        : { top: rect.bottom + 8 }),
    });
  }
  function delayHide() {
    timer.current = setTimeout(hide, 120);
  }
  useEffect(() => {
    if (!position) return;
    const key = (event: KeyboardEvent) => {
      if (event.key === "Escape") hide();
    };
    const outside = (event: PointerEvent) => {
      if (
        !trigger.current?.contains(event.target as Node) &&
        !bubble.current?.contains(event.target as Node)
      )
        hide();
    };
    window.addEventListener("keydown", key);
    window.addEventListener("pointerdown", outside);
    window.addEventListener("resize", hide);
    window.addEventListener("scroll", hide, true);
    return () => {
      window.removeEventListener("keydown", key);
      window.removeEventListener("pointerdown", outside);
      window.removeEventListener("resize", hide);
      window.removeEventListener("scroll", hide, true);
    };
  }, [position]);
  useEffect(
    () => () => {
      if (timer.current) clearTimeout(timer.current);
    },
    [],
  );
  if (!text) return null;
  return (
    <>
      <button
        ref={trigger}
        type="button"
        className="help-tip"
        aria-label={`About ${topic}`}
        aria-describedby={position ? id : undefined}
        aria-expanded={Boolean(position)}
        onMouseEnter={show}
        onMouseLeave={delayHide}
        onFocus={show}
        onBlur={hide}
        onClick={show}
      >
        <Info size={13} aria-hidden="true" />
      </button>
      {position &&
        createPortal(
          <div
            ref={bubble}
            id={id}
            role="tooltip"
            className="help-bubble"
            style={position}
            onMouseEnter={() => {
              if (timer.current) clearTimeout(timer.current);
            }}
            onMouseLeave={delayHide}
          >
            <strong>{topic}</strong>
            <p>{text}</p>
          </div>,
          document.body,
        )}
    </>
  );
}
