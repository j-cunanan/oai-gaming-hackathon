import assert from "node:assert/strict";
import test from "node:test";
import { allChecksPass, parseDiff } from "../src/diff.ts";

test("file headers are not changes and hunk line numbers follow additions/removals", () => {
  const [file] = parseDiff(
    "diff --git a/a.java b/a.java\nindex abc..def 100644\n--- a/a.java\n+++ b/a.java\n@@ -10,3 +10,3 @@ method\n context\n-old\n+new\n last\n",
  );
  assert.equal(file.path, "a.java");
  assert.equal(file.added, 1);
  assert.equal(file.removed, 1);
  assert.deepEqual(file.lines.at(-1), {
    kind: "context",
    text: "last",
    oldLine: 12,
    newLine: 12,
  });
  assert.equal(file.lines.find((line) => line.kind === "deletion").oldLine, 11);
  assert.equal(file.lines.find((line) => line.kind === "addition").newLine, 11);
});

test("multiple files and new-file hunks reset their positions", () => {
  const files = parseDiff(
    "diff --git a/a b/a\n--- a/a\n+++ /dev/null\n@@ -1 +0,0 @@\n-old\ndiff --git a/b b/b\nnew file mode 100644\n--- /dev/null\n+++ b/b\n@@ -0,0 +1,2 @@\n+one\n+two\n",
  );
  assert.deepEqual(
    files.map((f) => [f.path, f.added, f.removed]),
    [
      ["a", 0, 1],
      ["b", 2, 0],
    ],
  );
  assert.equal(files[1].lines.at(-1).newLine, 2);
});

test("source lines resembling headers remain visible changes", () => {
  const [file] = parseDiff(
    "--- a/x\n+++ b/x\n@@ -1 +1 @@\n--- old content\n+++ new content\n",
  );
  assert.equal(file.path, "x");
  assert.equal(file.removed, 1);
  assert.equal(file.added, 1);
  assert.equal(file.lines[1].text, "-- old content");
});

test("approval needs every named check and rejects incomplete or failed lists", () => {
  const checks = [
    "Regression before patch",
    "Candidate build",
    "Existing tests",
    "Original replay after patch",
    "Smoke test",
  ].map((name) => ({ name, status: "pass" }));
  assert.equal(allChecksPass(checks), true);
  assert.equal(allChecksPass(checks.slice(1)), false);
  assert.equal(
    allChecksPass([...checks, { name: "Existing tests", status: "fail" }]),
    false,
  );
  assert.equal(allChecksPass([]), false);
});
