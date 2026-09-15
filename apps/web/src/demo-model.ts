export type DemoSummary = {
  id: string;
  title: string;
  issue: number;
  summary: string;
  sampleReport: string;
  game: string;
  caseId: string;
  status: string;
  allPassed: boolean;
  matching: { label: string; pattern: string }[];
  negativePatterns: string[];
};
export type ReportMatch = {
  record: DemoSummary;
  strength: "strong" | "possible";
  reasons: string[];
  missing: string[];
};
export type DemoAction = {
  action: string;
  semantic: string;
  checkpoint: string;
  [key: string]: unknown;
};
export type DemoFrame = {
  url: string;
  sha256: string;
  label: string;
  checkpoint: string;
  eventSeq: number;
  recordedAt: string;
  log: string | null;
  process: { running: boolean; exit_code: number | null };
};
type Verdict = {
  observed: boolean;
  explanation: string;
  expected_state_reached?: boolean;
  symptom_absent?: boolean;
};
export type DemoDetail = {
  id: string;
  caseId: string;
  title: string;
  recordedAt: string;
  summary: string;
  targetCommit: string;
  report: { title: string; body: string; game: string; target_commit: string };
  status: string;
  allPassed: boolean;
  modelNote: string;
  assistance: string;
  scope: string;
  reductionNote: string;
  usage: { model_calls: number; input_tokens: number; output_tokens: number };
  elapsedSeconds: number;
  firstReproducedSeconds: number;
  reproduction: {
    successfulRuns: number;
    totalRuns: number;
    originalActions: number;
    steps: DemoAction[];
    oracle: { description: string; kind: string };
  };
  baseline: { phase: string; verdict: Verdict; frames: DemoFrame[] };
  candidate: {
    successfulRuns: number;
    totalRuns: number;
    followups: DemoAction[];
    verdict: Verdict;
    frames: DemoFrame[];
    outcomes: {
      recordedAt: string;
      eventSeq: number;
      fixed: boolean;
      expected: { explanation: string };
    }[];
  };
  findings: {
    root_cause: string;
    subsystem: string;
    candidates: {
      path: string;
      symbol: string | null;
      reasoning: string;
      evidence: string[];
    }[];
    limitations: string[];
  };
  patch: string;
  rationale: { explanation: string; risks: string[] };
  checks: {
    name: string;
    status: string;
    detail: string;
    artifact: string | null;
    baseline_artifact: string | null;
  }[];
  testCounts: {
    tests: number;
    failures: number;
    errors: number;
    skipped: number;
  } | null;
  milestones: {
    state: string;
    recordedAt: string;
    eventSeq: number;
    summary: string;
  }[];
  files: { pdf: string; patch: string; replay: string; evidence: string };
  provenance: {
    resultSha256: string;
    eventsSha256: string;
    artifactsSha256: string;
    assets: Record<string, string>;
  };
};
export const demoStages = [
  { id: "report", title: "Report", description: "Match the reported behavior" },
  {
    id: "reproduce",
    title: "Reproduce",
    description: "Follow the recorded trigger",
  },
  {
    id: "reduce",
    title: "Reduce",
    description: "Inspect the repeatable steps",
  },
  {
    id: "localize",
    title: "Diagnose",
    description: "Trace behavior into source",
  },
  { id: "patch", title: "Patch", description: "Review the AI proposal" },
  {
    id: "validate",
    title: "Validate",
    description: "Check what actually changed",
  },
  {
    id: "handoff",
    title: "Handoff",
    description: "Take the evidence with you",
  },
] as const;
export type DemoStage = (typeof demoStages)[number]["id"];

export function matchReport(
  report: string,
  game: string,
  catalog: DemoSummary[],
): ReportMatch[] {
  const text = report
    .slice(0, 30000)
    .toLowerCase()
    .replace(/[’‘]/g, "'")
    .replace(/\s+/g, " ")
    .trim();
  if (
    text.length < 10 ||
    game !== "mindustry" ||
    /\b(?:minecraft|factorio|luanti|minetest)\b/.test(text)
  )
    return [];
  const links = [
    ...text.matchAll(
      /https?:\/\/github\.com\/anuken\/mindustry\/issues\/(\d+)(?=[\s/#?.,)]|$)/g,
    ),
  ].map((m) => Number(m[1]));
  return catalog
    .flatMap((record) => {
      if (
        record.game !== game ||
        record.negativePatterns.some((p) => new RegExp(p, "i").test(text))
      )
        return [];
      if (links.includes(record.issue))
        return [
          {
            record,
            strength: "strong" as const,
            reasons: [`Exact Mindustry report #${record.issue}`],
            missing: [],
          },
        ];
      const found = record.matching.map((rule) =>
        new RegExp(rule.pattern, "i").test(text),
      );
      // The affected object must match. A generic "save crash" is insufficient.
      if (!found[0] || found.filter(Boolean).length < 2) return [];
      const reasons = record.matching
        .filter((_, i) => found[i])
        .map((rule) => rule.label);
      const missing = record.matching
        .filter((_, i) => !found[i])
        .map((rule) => rule.label);
      return [
        {
          record,
          strength: missing.length
            ? ("possible" as const)
            : ("strong" as const),
          reasons,
          missing,
        },
      ];
    })
    .sort(
      (a, b) =>
        Number(b.strength === "strong") - Number(a.strength === "strong") ||
        b.reasons.length - a.reasons.length,
    );
}

export function demoLocation(search: string): {
  id: string | null;
  stage: DemoStage;
} {
  const params = new URLSearchParams(search);
  const requested = params.get("stage");
  return {
    id: params.get("demo"),
    stage: demoStages.find((s) => s.id === requested)?.id ?? "report",
  };
}
