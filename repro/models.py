from datetime import UTC, datetime
from enum import StrEnum
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field, model_validator


def now() -> str:
    return datetime.now(UTC).isoformat()


class State(StrEnum):
    RECEIVED = "RECEIVED"
    TRIAGED = "TRIAGED"
    ENVIRONMENT_PREPARING = "ENVIRONMENT_PREPARING"
    READY = "READY"
    INVESTIGATING = "INVESTIGATING"
    REPRODUCED = "REPRODUCED"
    MINIMIZING = "MINIMIZING"
    REPRO_CONFIRMED = "REPRO_CONFIRMED"
    LOCALIZING = "LOCALIZING"
    TEST_GENERATING = "TEST_GENERATING"
    PATCH_PROPOSING = "PATCH_PROPOSING"
    VALIDATING = "VALIDATING"
    AWAITING_HUMAN = "AWAITING_HUMAN"
    COMPLETE = "COMPLETE"
    NOT_REPRODUCED = "NOT_REPRODUCED"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    ENVIRONMENT_UNSUPPORTED = "ENVIRONMENT_UNSUPPORTED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


ACTIVE_STATES = {
    State.ENVIRONMENT_PREPARING,
    State.INVESTIGATING,
    State.REPRODUCED,
    State.MINIMIZING,
    State.REPRO_CONFIRMED,
    State.LOCALIZING,
    State.TEST_GENERATING,
    State.PATCH_PROPOSING,
    State.VALIDATING,
}


class CaseInput(BaseModel):
    title: str = Field(min_length=3, max_length=250)
    body: str = Field(min_length=10, max_length=30000)
    game: Literal["mindustry", "luanti"] = "mindustry"
    target_commit: str = Field(pattern=r"^[0-9a-f]{40}$")
    platform: str = Field(default="Linux", max_length=100)
    build_version: str | None = Field(default=None, max_length=100)


class BugSpec(BaseModel):
    summary: str
    bug_class: str
    observed_behavior: str
    expected_behavior: str | None
    known_preconditions: list[str]
    uncertain_conditions: list[str]
    reproduction_hints: list[str]
    required_artifacts: list[str]
    severity: Literal["critical", "high", "medium", "low", "unknown"]
    confidence: float = Field(ge=0, le=1)


class Action(BaseModel):
    action: Literal["click", "double_click", "keypress", "type", "scroll", "move", "wait"]
    x: int | None = Field(default=None, ge=0, lt=1280)
    y: int | None = Field(default=None, ge=0, lt=720)
    keys: list[str] = Field(default_factory=list, max_length=5)
    text: str = Field(default="", max_length=2000)
    seconds: float = Field(default=0.5, ge=0, le=10)
    scroll_y: int = Field(default=0, ge=-20, le=20)
    button: Literal["left", "right", "middle"] = "left"
    semantic: str = Field(default="", max_length=500)

    @model_validator(mode="after")
    def coordinates(self):
        if self.action in {"click", "double_click", "move", "scroll"}:
            if self.x is None or self.y is None:
                raise ValueError("Pointer actions require x and y")
        if self.action == "keypress" and not self.keys:
            raise ValueError("keypress requires keys")
        return self


class OracleSpec(BaseModel):
    kind: Literal["visual", "crash", "log"]
    description: str = Field(min_length=5, max_length=2000)
    log_pattern: str | None = None


class Verdict(BaseModel):
    observed: bool
    confidence: float = Field(ge=0, le=1)
    explanation: str
    evidence: list[str]


class Hypothesis(BaseModel):
    id: str
    statement: str
    prediction: str
    status: Literal["untried", "supported", "rejected", "inconclusive"]
    observation: str


class LocalizationCandidate(BaseModel):
    path: str
    symbol: str | None
    score: float = Field(ge=0, le=1)
    evidence: list[str]
    reasoning: str


class Findings(BaseModel):
    root_cause: str
    subsystem: str
    candidates: list[LocalizationCandidate]
    limitations: list[str]


class Reproduction(BaseModel):
    version: int = 1
    game: str
    commit: str
    resolution: tuple[int, int] = (1280, 720)
    steps: list[Action]
    oracle: OracleSpec
    successful_runs: int = 0
    total_runs: int = 0
    original_actions: int = 0
    deterministic: bool = False
    evidence: list[str] = Field(default_factory=list)


class Usage(BaseModel):
    model_calls: int = 0
    input_tokens: int = 0
    output_tokens: int = 0


class Check(BaseModel):
    name: str
    status: Literal["pass", "fail", "not_run", "error"]
    detail: str
    artifact: str | None = None


class PatchRationale(BaseModel):
    explanation: str
    risks: list[str] = Field(default_factory=list)


class Case(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex[:12])
    report: CaseInput
    state: State = State.RECEIVED
    created_at: str = Field(default_factory=now)
    updated_at: str = Field(default_factory=now)
    summary: str = "Report received. Ready for triage."
    spec: BugSpec | None = None
    hypotheses: list[Hypothesis] = Field(default_factory=list)
    reproduction: Reproduction | None = None
    findings: Findings | None = None
    checks: list[Check] = Field(default_factory=list)
    usage: Usage = Field(default_factory=Usage)
    patch_artifact: str | None = None
    patch_rationale: PatchRationale | None = None
    latest_screenshot: str | None = None
    first_reproduced_seconds: float | None = None
    elapsed_seconds: float = 0
    owner_evidence: list[str] = Field(default_factory=list)
    benchmark_id: str | None = None


REQUIRED_VALIDATION_GATES = {
    "Regression before patch",
    "Candidate build",
    "Existing tests",
    "Original replay after patch",
    "Smoke test",
}


def patch_validated(case: Case) -> bool:
    checks = {check.name: check.status for check in case.checks}
    return bool(
        case.patch_artifact
        and REQUIRED_VALIDATION_GATES.issubset(checks)
        and all(status == "pass" for status in checks.values())
    )
