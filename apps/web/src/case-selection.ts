import { allChecksPass } from "./diff.ts";

type SelectableCase = {
  id: string;
  state: string;
  updated_at: string;
  checks: { name: string; status: string }[];
};
const progress = [
  "RECEIVED", "TRIAGED", "ENVIRONMENT_PREPARING", "READY", "INVESTIGATING",
  "REPRODUCED", "MINIMIZING", "REPRO_CONFIRMED", "LOCALIZING",
  "TEST_GENERATING", "PATCH_PROPOSING", "VALIDATING", "AWAITING_HUMAN", "COMPLETE",
];

export function preferredCase(cases: SelectableCase[]): string {
  const rank = (c: SelectableCase) => [
    Number(allChecksPass(c.checks)), progress.indexOf(c.state),
    Date.parse(c.updated_at) || 0,
  ];
  return cases.reduce<SelectableCase | undefined>((best, candidate) => {
    if (!best) return candidate;
    const a = rank(candidate), b = rank(best);
    for (let i = 0; i < a.length; i++) {
      if (a[i] !== b[i]) return a[i] > b[i] ? candidate : best;
    }
    return best;
  }, undefined)?.id ?? "";
}
