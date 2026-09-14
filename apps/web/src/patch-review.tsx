import { useMemo } from "react";
import {
  ArrowDownToLine,
  CheckCheck,
  FileCode2,
  GitPullRequest,
} from "lucide-react";
import { allChecksAccepted, allChecksPass, parseDiff } from "./diff";
import { HelpTip } from "./help";

type Props = {
  patch: string;
  error: string;
  downloadUrl: string | null;
  rationale: { explanation: string; risks: string[] } | null;
  checks: { name: string; status: string; detail: string }[];
};

export function PatchReview({
  patch,
  error,
  downloadUrl,
  rationale,
  checks,
}: Props) {
  const files = useMemo(() => parseDiff(patch), [patch]);
  const passed = allChecksPass(checks);
  const accepted = allChecksAccepted(checks);
  if (!downloadUrl)
    return (
      <div className="inspector-empty">
        <GitPullRequest />
        <p>
          A proposed patch appears after the bug is reproduced and its cause is
          diagnosed.
        </p>
      </div>
    );
  if (error)
    return (
      <div className="small-empty" role="alert">
        {error}
      </div>
    );
  if (!patch) return <div className="small-empty">Loading proposed patch…</div>;
  return (
    <div className="patch-review">
      <div className="patch-review-heading">
        <div>
          <span className="eyebrow">PROPOSED FIX</span>
          <h3>
            Proposed patch <HelpTip topic="Proposed patch" />
          </h3>
          <p>The source changes suggested for this bug.</p>
        </div>
        <a
          className="button secondary small"
          href={downloadUrl}
          download
          aria-label="Download patch"
        >
          <ArrowDownToLine size={14} /> .patch
        </a>
      </div>
      <div className="patch-explanation">
        <h4>
          Why this patch should work{" "}
          <HelpTip topic="Why this patch should work" />
        </h4>
        <p>
          {rationale?.explanation ||
            "No saved explanation is available for this patch."}
        </p>
        <h4>Risks and tradeoffs</h4>
        {rationale?.risks.length ? (
          <ul>
            {rationale.risks.map((risk, i) => (
              <li key={i}>{risk}</li>
            ))}
          </ul>
        ) : (
          <p className="muted">
            No specific risks were recorded. Review is still required.
          </p>
        )}
      </div>
      <div className={`patch-proof ${passed ? "passed" : ""}`}>
        <strong>
          <CheckCheck size={15} />
          {passed
            ? "All five validation checks passed"
            : accepted
              ? "Validation satisfied with pre-existing test failures"
              : "Validation is not complete"}
        </strong>
        {checks
          .filter((check) =>
            ["Regression before patch", "Original replay after patch"].includes(
              check.name,
            ),
          )
          .map((check) => (
            <p key={check.name}>
              <b>{check.name}:</b> {check.detail}
            </p>
          ))}
        <small>
          The recorded checks below show what was tested. Human approval is a
          separate step.
        </small>
      </div>
      <div className="diff-legend">
        <strong>
          Code changes <HelpTip topic="Changes" />
        </strong>
        <span className="diff-added">+ Added</span>
        <span className="diff-removed">− Removed</span>
        <span>Context unchanged</span>
      </div>
      {files.map((file, i) => (
        <section className="diff-file" key={i}>
          <header>
            <FileCode2 size={14} />
            <code>{file.path}</code>
            <span className="diff-count">
              <span className="diff-added">+{file.added}</span>{" "}
              <span className="diff-removed">−{file.removed}</span>
            </span>
          </header>
          <div className="diff-scroll">
            <table
              className="diff-table"
              aria-label={`Changes in ${file.path}`}
            >
              <thead>
                <tr>
                  <th>Old</th>
                  <th>New</th>
                  <th aria-label="Change type" />
                  <th>Source</th>
                </tr>
              </thead>
              <tbody>
                {file.lines.map((line, index) =>
                  line.kind === "hunk" || line.kind === "meta" ? (
                    <tr className={`diff-${line.kind}`} key={index}>
                      <td colSpan={4}>
                        <code>{line.text}</code>
                      </td>
                    </tr>
                  ) : (
                    <tr className={`diff-${line.kind}`} key={index}>
                      <td className="line-number">{line.oldLine}</td>
                      <td className="line-number">{line.newLine}</td>
                      <td className="diff-sign" aria-label={line.kind}>
                        {line.kind === "addition"
                          ? "+"
                          : line.kind === "deletion"
                            ? "−"
                            : ""}
                      </td>
                      <td className="diff-code">
                        <code>{line.text || " "}</code>
                      </td>
                    </tr>
                  ),
                )}
              </tbody>
            </table>
          </div>
        </section>
      ))}
      <p className="patch-note">
        Tested in the disposable game workspace. Download the patch for a
        reviewed upstream pull request.
      </p>
    </div>
  );
}
