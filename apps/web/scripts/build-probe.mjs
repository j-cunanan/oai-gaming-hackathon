import assert from "node:assert/strict";
import crypto from "node:crypto";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const repoRoot = path.resolve(
  fileURLToPath(new URL("../../..", import.meta.url)),
);
const source = path.join(repoRoot, "docs/evidence/3d-probe-2026-09-17");

export function buildProbe(
  output = path.join(repoRoot, "apps/web/public/probes/3d"),
) {
  const manifest = JSON.parse(
    fs.readFileSync(path.join(source, "manifest.json"), "utf8"),
  );
  assert.equal(manifest.version, 1);
  const files = Object.entries(manifest.files).map(([name, sha256]) => {
    assert(
      !path.isAbsolute(name) && !name.split("/").includes(".."),
      "Unsafe evidence path",
    );
    const bytes = fs.readFileSync(path.join(source, name));
    assert.equal(
      crypto.createHash("sha256").update(bytes).digest("hex"),
      sha256,
      `3D evidence changed: ${name}`,
    );
    return [name, bytes];
  });
  fs.mkdirSync(output, { recursive: true });
  for (const [name, bytes] of files) {
    const destination = path.join(output, name);
    fs.mkdirSync(path.dirname(destination), { recursive: true });
    fs.writeFileSync(destination, bytes);
  }
  fs.copyFileSync(
    path.join(source, "manifest.json"),
    path.join(output, "manifest.json"),
  );
  return manifest;
}

if (
  process.argv[1] &&
  path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)
) {
  const manifest = buildProbe();
  console.log(
    `Bundled ${manifest.runs.length} synthetic 3D trials, separately from real bug counts.`,
  );
}
