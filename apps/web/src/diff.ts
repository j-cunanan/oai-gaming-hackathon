export type DiffLine = {
  kind: "context" | "addition" | "deletion" | "hunk" | "meta";
  text: string;
  oldLine?: number;
  newLine?: number;
};
export type DiffFile = {
  path: string;
  added: number;
  removed: number;
  lines: DiffLine[];
};

export function parseDiff(diff: string): DiffFile[] {
  const files: DiffFile[] = [];
  let file: DiffFile | undefined;
  let oldLine = 0,
    newLine = 0,
    inHunk = false;
  for (const line of diff.replace(/\n$/, "").split("\n")) {
    if (line.startsWith("diff --git ") || !file) {
      file = { path: "Proposed change", added: 0, removed: 0, lines: [] };
      files.push(file);
      inHunk = false;
    }
    if (!inHunk && (line.startsWith("--- ") || line.startsWith("+++ "))) {
      const path = line
        .slice(4)
        .split("\t")[0]
        .replace(/^[ab]\//, "");
      if (path !== "/dev/null") file.path = path;
      continue;
    }
    if (
      line.startsWith("diff --git ") ||
      (!inHunk && line.startsWith("index "))
    )
      continue;
    const hunk = line.match(/^@@ -(\d+)(?:,\d+)? \+(\d+)(?:,\d+)? @@/);
    if (hunk) {
      oldLine = Number(hunk[1]);
      newLine = Number(hunk[2]);
      inHunk = true;
      file.lines.push({ kind: "hunk", text: line });
    } else if (inHunk && line.startsWith("+")) {
      file.added++;
      file.lines.push({
        kind: "addition",
        text: line.slice(1),
        newLine: newLine++,
      });
    } else if (inHunk && line.startsWith("-")) {
      file.removed++;
      file.lines.push({
        kind: "deletion",
        text: line.slice(1),
        oldLine: oldLine++,
      });
    } else if (inHunk && line.startsWith(" ")) {
      file.lines.push({
        kind: "context",
        text: line.slice(1),
        oldLine: oldLine++,
        newLine: newLine++,
      });
    } else if (line) {
      file.lines.push({ kind: "meta", text: line });
    }
  }
  return files.filter((file) => file.lines.length > 0);
}

export function allChecksPass(checks: { name: string; status: string }[]) {
  return (
    [
      "Regression before patch",
      "Candidate build",
      "Existing tests",
      "Original replay after patch",
      "Smoke test",
    ].every((name) =>
      checks.some((check) => check.name === name && check.status === "pass"),
    ) && checks.every((check) => check.status === "pass")
  );
}
