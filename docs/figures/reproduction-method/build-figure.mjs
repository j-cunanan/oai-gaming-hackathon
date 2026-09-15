/** One scene produces the SVG/PNG and an editable PowerPoint figure. */
import fs from "node:fs/promises";
import path from "node:path";
import { pathToFileURL } from "node:url";

const root = process.env.REPRO_REPO_ROOT || process.cwd();
const output =
  process.env.REPRO_FIGURE_OUTPUT ||
  path.join(root, "docs/figures/reproduction-method");
const build =
  process.env.REPRO_FIGURE_BUILD ||
  path.join(root, ".repro/reproduction-figure-build");
const modules = process.env.RUNTIME_NODE_MODULES;
const skill = process.env.PRESENTATION_SKILL_DIR;
const python = process.env.RUNTIME_PYTHON;
if (!modules || !skill || !python)
  throw new Error(
    "Set RUNTIME_NODE_MODULES, PRESENTATION_SKILL_DIR and RUNTIME_PYTHON.",
  );
const { Presentation, PresentationFile, FileBlob } = await import(
  pathToFileURL(path.join(modules, "@oai/artifact-tool/dist/artifact_tool.mjs"))
    .href
);
const { default: sharp } = await import(
  pathToFileURL(path.join(modules, "sharp/dist/index.mjs")).href
);
const { resolvePresentationFont, finalizePresentation } = await import(
  pathToFileURL(path.join(skill, "container_tools/artifact_tool_utils.mjs"))
    .href
);
const font = resolvePresentationFont({ fontFamily: "Arial" });
await fs.mkdir(output, { recursive: true });
await fs.mkdir(build, { recursive: true });

const W = 1600,
  H = 900;
const c = {
  bg: "#111116",
  white: "#F4F1FC",
  muted: "#B4AFC1",
  faint: "#90899E",
  purple: "#CBB8FF",
  purpleLine: "#786497",
  purpleFill: "#1C1827",
  line: "#37323F",
  green: "#9DE0BF",
  greenLine: "#527F6A",
  greenFill: "#17231D",
  red: "#F4A4AE",
};
const scene = [];
function box(x, y, w, h, fill = "none", stroke = "none", sw = 1.5, r = 0) {
  scene.push({ kind: "box", x, y, w, h, fill, stroke, sw, r });
}
function line(points, color = c.line, sw = 2) {
  scene.push({
    kind: "path",
    points,
    fill: "none",
    stroke: color,
    sw,
    closed: false,
  });
}
function arrow(points, color = c.purple, sw = 2.5, size = 9) {
  line(points, color, sw);
  const [x, y] = points.at(-1),
    [px, py] = points.at(-2);
  const theta = Math.atan2(y - py, x - px),
    bx = x - size * Math.cos(theta),
    by = y - size * Math.sin(theta);
  scene.push({
    kind: "path",
    points: [
      [x, y],
      [bx - size * 0.52 * Math.sin(theta), by + size * 0.52 * Math.cos(theta)],
      [bx + size * 0.52 * Math.sin(theta), by - size * 0.52 * Math.cos(theta)],
    ],
    fill: color,
    stroke: "none",
    sw: 0,
    closed: true,
  });
}
function text(
  x,
  y,
  w,
  value,
  size = 22,
  color = c.white,
  bold = false,
  align = "left",
  leading = 1.24,
) {
  String(value)
    .split("\n")
    .forEach((s, i) =>
      scene.push({
        kind: "text",
        x,
        y: y + i * size * leading,
        w,
        h: size * 1.3,
        value: s,
        size,
        color,
        bold,
        align,
      }),
    );
}

// Header. The accent wordmark follows the existing REPRO palette.
text(56, 36, 220, "REPRO", 25, c.purple, true);
text(56, 88, 1490, "How REPRO makes a bug repeatable", 50, c.white, true);
text(
  56,
  158,
  1490,
  "AI discovers the trigger. A frozen replay must reproduce it on fresh game profiles.",
  24,
  c.muted,
);

// Main flow: preparation, adaptive discovery, controlled replay, regression artifact.
box(318, 228, 444, 430, c.purpleFill, c.purpleLine, 1.5, 10);
box(810, 228, 424, 430, c.greenFill, c.greenLine, 1.5, 10);
text(56, 244, 225, "01  DEFINE", 18, c.faint, true);
text(56, 279, 242, "Player report", 28, c.white, true);
text(
  56,
  344,
  235,
  "“The deleted patch\ncomes back after\nI reopen my map.”",
  23,
  c.purple,
);
text(
  56,
  474,
  235,
  "Pin the game revision\nand expected behavior.",
  21,
  c.muted,
);
text(56, 563, 236, "The report defines\nwhat counts as the bug.", 21, c.muted);
arrow(
  [
    [272, 418],
    [308, 418],
  ],
  c.purple,
);

text(344, 244, 390, "02  DISCOVER", 18, c.purple, true);
text(344, 279, 392, "AI explores the game", 28, c.white, true);
box(340, 370, 154, 88, "#282032", c.purpleLine, 1.5, 5);
box(592, 370, 154, 88, "#282032", c.purpleLine, 1.5, 5);
text(347, 385, 140, "AI\ninvestigator", 23, c.white, true, "center");
text(599, 385, 140, "Game\nsandbox", 23, c.white, true, "center");
text(498, 359, 90, "inputs", 17, c.purple, false, "center");
arrow(
  [
    [501, 393],
    [584, 393],
  ],
  c.purple,
  2.2,
  8,
);
arrow(
  [
    [584, 432],
    [501, 432],
  ],
  c.purple,
  2.2,
  8,
);
text(496, 440, 94, "screenshots", 15, c.muted, false, "center");
text(340, 480, 177, "Hypothesize", 21, c.white, true);
text(340, 513, 190, "Choose next input", 19, c.muted);
text(592, 480, 162, "Linux desktop", 20, c.white, true);
text(592, 513, 160, "Isolated in Docker", 18, c.muted);
line(
  [
    [344, 550],
    [736, 550],
  ],
  c.purpleLine,
  1,
);
text(344, 568, 390, "Record inputs + resulting evidence", 21, c.white, true);
text(344, 603, 390, "Check the first attempt before replay.", 20, c.muted);
text(756, 358, 64, "Freeze\ntrace", 16, c.purple, true, "center");
arrow(
  [
    [770, 418],
    [801, 418],
  ],
  c.purple,
);

text(836, 244, 372, "03  VERIFY", 18, c.green, true);
text(836, 279, 374, "Replay from a clean state", 26, c.white, true);
text(836, 338, 374, "5 fresh profiles by default", 22, c.white);
for (let i = 0; i < 5; i++) {
  const x = 836 + i * 74;
  box(x, 388, 58, 60, "#22392D", c.greenLine, 1.5, 4);
  text(x, 400, 58, String(i + 1), 26, c.green, true, "center");
  if (i < 4)
    arrow(
      [
        [x + 62, 418],
        [x + 70, 418],
      ],
      c.green,
      1.6,
      4,
    );
}
text(836, 466, 374, "All 5 must show the defect", 20, c.green, true);
line(
  [
    [836, 504],
    [1208, 504],
  ],
  c.greenLine,
  1,
);
text(836, 523, 374, "Judge each run's checkpoints", 23, c.white, true);
text(836, 563, 374, "Original symptom + 2–8 images", 21, c.muted);
text(836, 599, 374, "Separate verification call", 21, c.green, true);
text(836, 632, 374, "Incomplete evidence stays inconclusive.", 17, c.muted);
arrow(
  [
    [1242, 418],
    [1278, 418],
  ],
  c.green,
);

text(1292, 244, 252, "04  RETAIN", 18, c.faint, true);
text(1292, 279, 252, "A regression test", 27, c.white, true);
text(1292, 338, 250, "Reduce, then reconfirm", 22, c.white, true);
text(1292, 374, 252, "Preserve required checkpoints.", 18, c.muted);
box(1292, 427, 252, 137, "#201D28", c.line, 1.5, 4);
text(1310, 442, 216, "repro.yaml", 25, c.purple, true);
text(1310, 482, 218, "Revision + inputs\nCheckpoints + bug check", 19, c.muted);
text(
  1292,
  593,
  252,
  "Replay the same trigger\non a candidate patch.",
  21,
  c.muted,
);

// Concrete temporal example. Labels describe states, not fabricated screenshots.
line(
  [
    [56, 671],
    [1544, 671],
  ],
  c.line,
  1.5,
);
text(
  56,
  692,
  1488,
  "The key check: did the deletion survive saving and reopening?",
  28,
  c.white,
  true,
);
const stages = [
  {
    x: 56,
    w: 254,
    title: "Saved patch",
    sub: "Initial save is visible",
    color: c.purple,
  },
  {
    x: 362,
    w: 225,
    title: "Delete",
    sub: "Empty list is visible",
    color: c.white,
  },
  {
    x: 665,
    w: 240,
    title: "Confirm save",
    sub: "Save success is visible",
    color: c.white,
  },
  {
    x: 971,
    w: 252,
    title: "Reopen map",
    sub: "Same map is verified",
    color: c.white,
  },
  {
    x: 1277,
    w: 267,
    title: "Patch returns",
    sub: "Reported defect is visible",
    color: c.red,
  },
];
stages.forEach((s, i) => {
  text(s.x, 749, s.w, s.title, 25, s.color, true);
  text(s.x, 785, s.w, s.sub, 18, c.muted);
  if (i < 4)
    arrow(
      [
        [s.x + s.w + 6, 767],
        [stages[i + 1].x - 20, 767],
      ],
      c.faint,
      2,
      7,
    );
});
text(
  56,
  824,
  1488,
  "Recorded Mindustry #12620: 5/5 baseline runs, 31 actions reduced to 30, and 5/5 correct candidate outcomes.",
  20,
  c.muted,
);
text(
  56,
  852,
  1488,
  "This run received save-checkpoint guidance. Visual verification uses model judgments.",
  16,
  c.faint,
);

const xml = (s) =>
  String(s)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
function svgForScene(transparent = false) {
  const content = scene
    .map((o) => {
      if (o.kind === "text")
        return `<text x="${o.x + (o.align === "center" ? o.w / 2 : o.align === "right" ? o.w : 0)}" y="${o.y + o.size * 0.92}" font-size="${o.size}" font-weight="${o.bold ? 700 : 400}" fill="${o.color}" text-anchor="${o.align === "center" ? "middle" : o.align === "right" ? "end" : "start"}">${xml(o.value)}</text>`;
      if (o.kind === "box")
        return `<rect x="${o.x}" y="${o.y}" width="${o.w}" height="${o.h}" rx="${o.r || 0}" fill="${o.fill}" stroke="${o.stroke}" stroke-width="${o.sw}"/>`;
      if (o.kind === "ellipse")
        return `<ellipse cx="${o.x + o.w / 2}" cy="${o.y + o.h / 2}" rx="${o.w / 2}" ry="${o.h / 2}" fill="${o.fill}" stroke="${o.stroke}" stroke-width="${o.sw}"/>`;
      return `<path d="${o.points.map((p, i) => `${i ? "L" : "M"} ${p[0]} ${p[1]}`).join(" ")}${o.closed ? " Z" : ""}" fill="${o.fill}" stroke="${o.stroke}" stroke-width="${o.sw}" stroke-linejoin="round"/>`;
    })
    .join("\n");
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}" role="img" aria-labelledby="title desc"><title id="title">How REPRO makes a bug repeatable</title><desc id="desc">A player report defines the symptom and game revision. An AI investigator experiments in an isolated game while recording inputs and evidence. A fixed replay runs on five fresh profiles by default. A separate model call verifies the original symptom using ordered checkpoint images. Action reduction preserves those checkpoints and reconfirms any shorter trace. The resulting YAML replay becomes a regression for a candidate patch. The Mindustry data-patch example requires visible saves, deletion and reopening of the same map.</desc>${transparent ? "" : `<rect width="${W}" height="${H}" fill="${c.bg}"/>`}<g font-family="${font}, Liberation Sans, sans-serif">${content}</g></svg>`;
}
const svg = svgForScene();
await fs.writeFile(path.join(output, "repro-reproduction.svg"), svg);
await fs.writeFile(
  path.join(output, "repro-reproduction-transparent.svg"),
  svgForScene(true),
);

const presentation = Presentation.create({
  slideSize: { width: W, height: H },
});
const slide = presentation.slides.add();
slide.background.fill = c.bg;
for (const [i, o] of scene.entries()) {
  if (o.kind === "text") {
    const shape = slide.shapes.add({
      geometry: "textbox",
      name: `text-${i}`,
      position: { left: o.x, top: o.y, width: o.w, height: o.h },
      fill: "none",
      line: { fill: "none", width: 0 },
    });
    shape.text = o.value;
    shape.text.style = {
      typeface: font,
      fontSize: o.size,
      bold: o.bold,
      color: o.color,
      alignment: o.align,
      verticalAlignment: "top",
      autoFit: "none",
      wrap: "none",
      insets: { top: 0, right: 0, bottom: 0, left: 0 },
    };
  } else if (o.kind === "box" || o.kind === "ellipse") {
    slide.shapes.add({
      geometry: o.kind === "ellipse" ? "ellipse" : "rect",
      name: `shape-${i}`,
      position: { left: o.x, top: o.y, width: o.w, height: o.h },
      fill: o.fill,
      line: { fill: o.stroke, width: o.sw },
      ...(o.r ? { borderRadius: o.r } : {}),
    });
  } else {
    const xs = o.points.map((p) => p[0]),
      ys = o.points.map((p) => p[1]);
    const x = Math.min(...xs),
      y = Math.min(...ys),
      w = Math.max(1, Math.max(...xs) - x),
      h = Math.max(1, Math.max(...ys) - y);
    slide.shapes.add({
      geometry: "custom",
      name: `connector-${i}`,
      position: { left: x, top: y, width: w, height: h },
      fill: o.fill,
      line: { fill: o.stroke, width: o.sw },
      customPaths: [
        {
          width: w,
          height: h,
          commands: [
            ...o.points.map((p, j) => ({
              [j ? "lineTo" : "moveTo"]: { x: p[0] - x, y: p[1] - y },
            })),
            ...(o.closed ? [{ close: {} }] : []),
          ],
        },
      ],
    });
  }
}
const sources = [
  "https://github.com/j-cunanan/oai-gaming-hackathon/blob/1aa7839/repro/orchestration/manager.py",
  "https://github.com/j-cunanan/oai-gaming-hackathon/blob/1aa7839/repro/agents/oracle.py",
  "https://github.com/j-cunanan/oai-gaming-hackathon/blob/1aa7839/repro/computer/replay.py",
  "https://github.com/j-cunanan/oai-gaming-hackathon/blob/1aa7839/repro/computer/sandbox.py",
  "https://github.com/j-cunanan/oai-gaming-hackathon/blob/1aa7839/docs/demos/datapatch-2026-09-15/README.md",
];
slide.speakerNotes.textFrame.setText(
  `REPRO converts an adaptive search for a trigger into a fixed, inspectable replay. During discovery the investigator chooses inputs based on screenshots, process state and logs. Before confirming a proposed trigger, verification uses the triaged report symptom rather than the investigator's conclusion. A replay resets the worker and game profile, restores registered fixtures where present, and executes the recorded actions. The default is five repetitions; all must reproduce before the workflow advances.\n\nFor temporal bugs a separate model call receives 2–8 ordered checkpoint screenshots plus the input trace. It must establish the prerequisite state and transition. Missing, low-confidence or contradictory evidence is inconclusive. Crash and literal-log checks instead inspect process state or a log signature. This figure emphasizes the temporal path used by the presentation case.\n\nReduction only deletes recorded actions, preserves required checkpoints and their order, and reconfirms the shorter sequence. It is bounded and does not prove a globally minimal trigger. The retained YAML is a replay regression; source diagnosis, patch proposal and full candidate validation follow. Candidate replays must reach the expected state and show the symptom absent, with separately frozen follow-up steps where the original crash or log trigger does not prove the positive outcome.\n\nThe recorded Mindustry #12620 case is md-12620-terra-overnight-02. It received guidance to include both successful-save confirmations. Its original report-only predecessor confirmed 3/5. The shown run confirmed 5/5 baseline and 5/5 candidate outcomes and reduced 31 actions to 30. Visual judgments are model-based evidence rather than deterministic ground truth. These are recorded results, not a fresh execution.\n\nSources, inspected at repository revision 1aa7839:\n${sources.join("\n")}`,
);

const candidate = path.join(build, "candidate.pptx");
const final = path.join(output, "repro-reproduction-editable.pptx");
await (await PresentationFile.exportPptx(presentation)).save(candidate);
await finalizePresentation({
  workspaceDir: root,
  candidatePath: candidate,
  finalPath: final,
  pythonExecutable: python,
  explicitTotalSlideCount: 1,
  requiredNativeTableOwnerSlides: [],
  requiredNativeChartOwnerSlides: [],
  integrityValidatorPath: path.join(
    skill,
    "container_tools/inspect_presentation_package_integrity.py",
  ),
  layoutValidatorPath: path.join(
    skill,
    "container_tools/inspect_presentation_layout_geometry.py",
  ),
  layoutArgs: [
    "--expected-slide-size-emu",
    `${W * 9525},${H * 9525}`,
    "--validate-bullet-geometry",
    "--validate-heading-fit",
  ],
  fontPolicy: { basis: "design", families: [font] },
  verifyArtifactToolImport: true,
  receiptPath: path.join(build, "repro-reproduction.validation.json"),
});
const checked = await PresentationFile.importPptx(await FileBlob.load(final));
const preview = await checked.export({
  slide: checked.slides.items[0],
  format: "png",
  scale: 1,
});
await fs.writeFile(
  path.join(build, "final-slide.png"),
  new Uint8Array(await preview.arrayBuffer()),
);
const large = await checked.export({
  slide: checked.slides.items[0],
  format: "png",
  scale: 2,
});
await fs.writeFile(
  path.join(output, "repro-reproduction.png"),
  new Uint8Array(await large.arrayBuffer()),
);
await sharp(Buffer.from(svgForScene(true)))
  .resize(W * 2, H * 2)
  .png()
  .toFile(path.join(output, "repro-reproduction-transparent.png"));
console.log(
  JSON.stringify({
    output,
    objects: scene.length,
    slideCount: 1,
    pngSize: [W * 2, H * 2],
  }),
);
