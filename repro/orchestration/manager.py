import asyncio
import time
from typing import Literal

import yaml
from pydantic import BaseModel, Field

from repro.agents.openai import BudgetExceeded, Model, Tool
from repro.agents.oracle import verify
from repro.computer.recorder import Recorder
from repro.computer.replay import replay
from repro.computer.sandbox import DockerSandbox
from repro.config import Settings
from repro.minimization.ddmin import minimize
from repro.minimization.semantic import propose_reduction
from repro.models import (
    Action,
    BugSpec,
    Case,
    Check,
    Findings,
    Hypothesis,
    OracleSpec,
    PatchRationale,
    Reproduction,
    State,
    patch_validated,
)
from repro.storage.store import Store


class Empty(BaseModel):
    pass


class ReadSource(BaseModel):
    path: str
    start_line: int = Field(ge=1)
    line_count: int = Field(ge=1, le=240)


class SearchSource(BaseModel):
    query: str = Field(min_length=1, max_length=200)


class InvestigationResult(BaseModel):
    outcome: Literal["observed", "not_reproduced", "insufficient_evidence"]
    summary: str
    oracle: OracleSpec | None
    limitations: list[str]


class PatchProposal(BaseModel):
    diff: str = Field(min_length=20, max_length=60000)
    explanation: str
    risks: list[str]


class FixedVerdict(BaseModel):
    expected_state_reached: bool
    symptom_absent: bool
    confidence: float = Field(ge=0, le=1)
    explanation: str


class Manager:
    def __init__(self, settings: Settings, store: Store):
        self.settings, self.store = settings, store

    def record_failure(self, case: Case, exc: Exception, state=State.FAILED):
        detail = str(exc) or type(exc).__name__
        self.store.artifact(case.id, "worker-error.log", detail)
        summary = detail.splitlines()[0][:250]
        self.store.transition(
            case, state, f"{summary} Inspect worker-error.log in Evidence for details."
        )

    async def prepare(self, case: Case):
        sandbox = DockerSandbox(self.settings, self.store, case)
        self.store.transition(
            case,
            State.ENVIRONMENT_PREPARING,
            "Fetching the exact revision and preparing build dependencies.",
        )
        try:
            await sandbox.prepare()
            self.store.transition(
                case,
                State.READY,
                "Build prepared. Investigation uses an isolated desktop with game network access disabled.",
            )
        except asyncio.CancelledError:
            await sandbox.stop()
            self.store.transition(
                case, State.CANCELLED, "Preparation cancelled; artifacts retained."
            )
            raise
        except Exception as exc:
            self.record_failure(case, exc, State.ENVIRONMENT_UNSUPPORTED)

    def source_tools(self, sandbox):
        async def read(args):
            return {
                "source": await sandbox.read_source(args.path, args.start_line, args.line_count)
            }

        async def search(args):
            return {"matches": await sandbox.search(args.query)}

        return [
            Tool(
                "read_source",
                "Read a file in the pre-fix repository with line numbers.",
                ReadSource,
                read,
            ),
            Tool(
                "search_source",
                "Search the pre-fix repository using ripgrep. No internet or future history.",
                SearchSource,
                search,
            ),
        ]

    async def replay_case(self, case: Case, *, baseline=True):
        if not case.reproduction:
            raise ValueError("This case has no recorded reproduction")
        sandbox = DockerSandbox(self.settings, self.store, case)
        sandbox.use_baseline = baseline
        model = Model(self.settings, self.store, case)
        recorder = Recorder(self.store, case, sandbox)
        try:
            async with asyncio.timeout(self.settings.max_seconds):
                verdict, _ = await replay(
                    sandbox,
                    recorder,
                    model,
                    case.reproduction.steps,
                    case.reproduction.oracle,
                    phase="manual-baseline" if baseline else "manual-candidate",
                )
                return verdict
        finally:
            await sandbox.stop()
            await model.close()

    async def validate_case(self, case: Case):
        if not case.patch_artifact or not case.reproduction:
            raise ValueError("A candidate patch and recorded reproduction are required")
        started = time.monotonic()
        sandbox = DockerSandbox(self.settings, self.store, case)
        model = Model(self.settings, self.store, case)
        recorder = Recorder(self.store, case, sandbox)
        try:
            self.store.artifact(
                case.id,
                "validation-before-rerun.json",
                case.model_dump_json(indent=2),
                "application/json",
            )
            case.checks = []
            async with asyncio.timeout(self.settings.max_seconds):
                self.store.transition(
                    case,
                    State.VALIDATING,
                    "Rechecking the original trigger on fresh baseline runs.",
                )
                self.store.save(
                    case,
                    "validation_environment",
                    {
                        "network": "none",
                        "phase": "fresh baseline replays",
                        "worker_image": self.settings.worker_image,
                    },
                )
                rep = case.reproduction
                rep.successful_runs = rep.total_runs = 0
                rep.evidence = []
                rep.deterministic = False
                sandbox.use_baseline = True
                for _ in range(self.settings.repetitions):
                    verdict, _ = await replay(
                        sandbox,
                        recorder,
                        model,
                        rep.steps,
                        rep.oracle,
                        phase="baseline-revalidation",
                    )
                    rep.total_runs += 1
                    rep.successful_runs += int(verdict.observed)
                    rep.evidence.extend(verdict.evidence)
                    self.store.save(case)
                sandbox.use_baseline = False
                rep.deterministic = rep.successful_runs == rep.total_runs
                case.checks.append(
                    Check(
                        name="Regression before patch",
                        status="pass" if rep.deterministic else "fail",
                        detail=f"Trigger observed in {rep.successful_runs}/{rep.total_runs} fresh baseline runs.",
                    )
                )
                self.save_replay(case)
                await self.validate(case, sandbox, model, recorder)
            self.store.transition(
                case,
                State.AWAITING_HUMAN,
                "All validation gates passed. Ready for handoff review."
                if patch_validated(case)
                else "Validation is incomplete or failed. Inspect the recorded gates.",
            )
        except asyncio.CancelledError:
            self.store.transition(
                case, State.CANCELLED, "Validation cancelled. Partial checks retained."
            )
            raise
        except Exception as exc:
            self.record_failure(case, exc)
        finally:
            await sandbox.stop()
            await model.close()
            case.elapsed_seconds += time.monotonic() - started
            self.store.save(case)
            self.store.artifact(case.id, "report.md", self.report(case), "text/markdown")

    async def refine_case(self, case: Case):
        if not case.reproduction or not case.reproduction.deterministic:
            raise ValueError("A confirmed reproduction is required")
        started = time.monotonic()
        sandbox = DockerSandbox(self.settings, self.store, case)
        sandbox.use_baseline = True
        model = Model(self.settings, self.store, case)
        recorder = Recorder(self.store, case, sandbox)
        try:
            async with asyncio.timeout(self.settings.max_seconds):
                original_steps = list(case.reproduction.steps)
                if case.checks:
                    self.store.artifact(
                        case.id,
                        "validation-before-reduction.json",
                        case.model_dump_json(indent=2),
                        "application/json",
                    )
                await self.reduce_replay(case, sandbox, model, recorder)
                if case.reproduction.steps != original_steps:
                    # Previously recorded checks concern a different replay. Retain their audit.
                    rep = case.reproduction
                    case.checks = [
                        Check(
                            name="Regression before patch",
                            status="pass",
                            detail=f"Reduced trigger observed in {rep.successful_runs}/{rep.total_runs} clean baseline runs.",
                        )
                    ]
                    self.store.save(case)
                    if case.patch_artifact:
                        sandbox.use_baseline = False
                        await self.validate(case, sandbox, model, recorder)
                self.store.transition(
                    case,
                    State.AWAITING_HUMAN if case.patch_artifact else State.REPRO_CONFIRMED,
                    "Replay refinement finished. Inspect the recorded reduction and validation checks.",
                )
        except asyncio.CancelledError:
            self.store.transition(
                case, State.CANCELLED, "Replay refinement cancelled; evidence retained."
            )
            raise
        except (BudgetExceeded, TimeoutError) as exc:
            self.store.transition(
                case,
                State.INSUFFICIENT_EVIDENCE,
                str(exc) or "Replay refinement time budget exhausted; evidence retained.",
            )
        except Exception as exc:
            self.record_failure(case, exc)
        finally:
            await sandbox.stop()
            await model.close()
            case.elapsed_seconds += time.monotonic() - started
            self.store.save(case)
            self.store.artifact(case.id, "report.md", self.report(case), "text/markdown")

    async def investigate(self, case: Case):
        started = time.monotonic()
        model = None
        sandbox = DockerSandbox(self.settings, self.store, case)
        try:
            model = Model(self.settings, self.store, case)
            async with asyncio.timeout(self.settings.max_seconds):
                await self._investigate(case, sandbox, model, started)
        except asyncio.CancelledError:
            self.store.transition(
                case, State.CANCELLED, "Investigation cancelled; all recorded evidence is retained."
            )
            raise
        except (BudgetExceeded, TimeoutError) as exc:
            self.store.transition(
                case,
                State.INSUFFICIENT_EVIDENCE,
                str(exc) or "Time budget exhausted; partial findings and evidence retained.",
            )
        except Exception as exc:
            self.record_failure(case, exc)
        finally:
            await sandbox.stop()
            if model:
                await model.close()
            case.elapsed_seconds += time.monotonic() - started
            self.store.save(case)
            self.store.artifact(case.id, "report.md", self.report(case), "text/markdown")

    async def _investigate(self, case: Case, sandbox: DockerSandbox, model: Model, started):
        self.store.save(
            case, "stage_started", {"stage": "triage", "summary": "Starting report triage."}
        )
        if not case.spec:
            case.spec = await model.structured(
                BugSpec,
                "Normalize this player report. Do not diagnose a cause or assume the issue is real. "
                "List missing artifacts and uncertainties explicitly.\n"
                + case.report.model_dump_json(),
                purpose="triage",
            )
        self.store.transition(case, State.TRIAGED, case.spec.summary)
        if not (sandbox.repo / ".git").exists() or not (sandbox.root / "prepared.json").exists():
            await self.prepare(case)
            if case.state != State.READY:
                return
        recorder = Recorder(self.store, case, sandbox)
        observation = recorder.capture(await sandbox.reset(), "initial")
        if not observation.get("process", {}).get("running"):
            self.store.transition(
                case,
                State.ENVIRONMENT_UNSUPPORTED,
                "The prepared game did not remain running. Inspect the launch log.",
            )
            return
        self.store.transition(
            case, State.INVESTIGATING, "Testing the player report in the historical game build."
        )
        result = None
        verified_observation = None
        discovery_actions = []

        async def computer(action):
            if len(discovery_actions) >= self.settings.max_actions:
                raise BudgetExceeded("Computer action budget exhausted")
            observation = await recorder.act(action)
            discovery_actions.append(action)
            return observation

        async def observe(_):
            return await recorder.observe()

        async def reset(_):
            discovery_actions.clear()
            recorder.previous_log = ""
            self.store.save(
                case,
                "reset",
                {"summary": "Restoring clean profile and launching a fresh game process."},
            )
            return recorder.capture(await sandbox.reset(), "reset")

        async def hypothesis(args):
            case.hypotheses = [h for h in case.hypotheses if h.id != args.id] + [args]
            self.store.save(case, "hypothesis", args.model_dump())
            return {"recorded": True}

        async def finish(args):
            nonlocal result, verified_observation
            if args.outcome == "observed" and not args.oracle:
                raise ValueError("An observed symptom requires an independently checkable oracle")
            if args.outcome == "observed":
                # The report defines the symptom. An investigator cannot redefine success.
                args.oracle.description = case.spec.observed_behavior
                observation = await recorder.observe()
                proof = await verify(model, args.oracle, observation, launched_ok=True)
                self.store.save(case, "verification", proof.model_dump())
                if not proof.observed:
                    return {
                        **observation,
                        "accepted": False,
                        "verification": proof.model_dump(),
                        "next_step": "This screenshot did not prove the reported symptom. Continue testing another view or hypothesis, or finish honestly as not_reproduced. Do not mistake the bottom of a viewport for the end of a scrollable panel.",
                    }
                verified_observation = proof
            result = args
            return {"recorded": True, "verification": "Independent replay verification follows."}

        tools = [
            Tool(
                "computer",
                "Perform one desktop action. Scroll positive=up, negative=down. Keys use pyautogui names (esc, enter, ctrl). Waits settle the UI.",
                Action,
                computer,
            ),
            Tool("observe", "Get a fresh screenshot, game process state and logs.", Empty, observe),
            Tool(
                "reset",
                "Discard the current experiment and restart from a clean game profile.",
                Empty,
                reset,
            ),
            Tool(
                "hypothesis",
                "Record a concise hypothesis and observable experiment result.",
                Hypothesis,
                hypothesis,
            ),
            *self.source_tools(sandbox),
            Tool(
                "finish",
                "Conclude this attempt with a concrete oracle, or an honest inability to reproduce.",
                InvestigationResult,
                finish,
            ),
        ]
        await model.loop(
            "Investigate the following report in the running game. First handle any first-run dialogs. "
            "Use the UI to test hypotheses. Every action will be replayed from a clean profile, including startup dialogs. "
            "You may search the code to understand navigation, but source matches alone never verify behavior. "
            "For a visual bug, end with the symptom clearly visible in one screenshot. "
            "Record at least one hypothesis and its result. Then call finish.\n"
            + case.spec.model_dump_json(),
            tools,
            purpose="game investigation",
            done=lambda: result is not None,
            observation=observation,
            max_turns=min(45, self.settings.max_model_calls),
        )
        if result.outcome != "observed":
            state = (
                State.NOT_REPRODUCED
                if result.outcome == "not_reproduced"
                else State.INSUFFICIENT_EVIDENCE
            )
            self.store.transition(case, state, result.summary)
            return
        verdict = verified_observation
        case.first_reproduced_seconds = time.monotonic() - started
        rep = case.reproduction = Reproduction(
            game=case.report.game,
            commit=case.report.target_commit,
            steps=list(discovery_actions),
            oracle=result.oracle,
            original_actions=len(discovery_actions),
            evidence=verdict.evidence,
        )
        self.store.transition(
            case,
            State.REPRODUCED,
            "Symptom observed and independently checked. Repeating from a clean profile.",
        )
        for _ in range(self.settings.repetitions):
            check, _ = await replay(
                sandbox, recorder, model, rep.steps, rep.oracle, phase="confirmation"
            )
            rep.total_runs += 1
            rep.successful_runs += int(check.observed)
            rep.evidence.extend(check.evidence)
            self.store.save(case)
        rep.deterministic = rep.successful_runs == rep.total_runs and rep.total_runs >= 2
        if not rep.deterministic:
            self.save_replay(case)
            self.store.transition(
                case,
                State.INSUFFICIENT_EVIDENCE,
                f"Observed in {rep.successful_runs}/{rep.total_runs} fresh replays. A stable trigger still needs investigation.",
            )
            return
        await self.reduce_replay(case, sandbox, model, recorder)
        self.store.transition(
            case,
            State.REPRO_CONFIRMED,
            f"Verified in {rep.successful_runs}/{rep.total_runs} replays; {rep.original_actions} → {len(rep.steps)} actions.",
        )
        await self.localize(case, sandbox, model)
        self.store.transition(
            case,
            State.TEST_GENERATING,
            "Saving the confirmed replay as an executable regression test.",
        )
        case.checks = [
            Check(
                name="Regression before patch",
                status="pass",
                detail=f"Bug oracle triggered in {rep.successful_runs}/{rep.total_runs} clean runs; the regression therefore fails on the pre-fix build.",
            )
        ]
        await self.propose(case, sandbox, model)
        if case.patch_artifact:
            await self.validate(case, sandbox, model, recorder)
        self.store.transition(
            case,
            State.AWAITING_HUMAN,
            "Candidate ready for review. "
            + (
                "All validation gates passed."
                if patch_validated(case)
                else "Validation is incomplete or failed; inspect the recorded checks before using the patch."
            ),
        )

    async def reduce_replay(self, case, sandbox, model, recorder):
        self.store.transition(
            case,
            State.MINIMIZING,
            "Proposing action deletions and accepting them only after fresh baseline replays.",
        )
        rep = case.reproduction

        async def reproduces(steps):
            check, _ = await replay(
                sandbox, recorder, model, steps, rep.oracle, phase="minimization"
            )
            return check.observed

        current, trials = list(rep.steps), 0
        # Leave room for repeated confirmation, source work and post-patch verification.
        if len(current) > 1 and model.remaining_calls > 24:
            try:
                candidate, proposal = await propose_reduction(model, current, rep.oracle)
                self.store.save(case, "reduction_proposal", proposal.model_dump())
                if len(candidate) < len(current):
                    trials += 1
                    if await reproduces(candidate):
                        current = candidate
            except ValueError as exc:
                self.store.save(case, "reduction_proposal_rejected", {"reason": str(exc)})
        trial_budget = min(10 - trials, max(0, model.remaining_calls - 23))
        reduced, dd_trials = await minimize(current, reproduces, max_trials=trial_budget)
        trials += dd_trials
        successes, evidence = 0, []
        if reduced != rep.steps:
            for _ in range(self.settings.repetitions):
                check, _ = await replay(
                    sandbox, recorder, model, reduced, rep.oracle, phase="reduced-confirmation"
                )
                successes += int(check.observed)
                evidence.extend(check.evidence)
            if successes == self.settings.repetitions:
                rep.steps, rep.evidence = reduced, evidence
                rep.successful_runs = successes
                rep.total_runs = self.settings.repetitions
        self.store.save(
            case,
            "minimization",
            {
                "original": rep.original_actions,
                "reduced": len(rep.steps),
                "trials": trials,
                "candidate_confirmation_successes": successes,
                "bounded": True,
            },
        )
        self.save_replay(case)

    def save_replay(self, case):
        self.store.artifact(
            case.id,
            "repro.yaml",
            yaml.safe_dump(case.reproduction.model_dump(mode="json"), sort_keys=False),
            "application/yaml",
        )

    async def localize(self, case, sandbox, model):
        self.store.transition(
            case, State.LOCALIZING, "Tracing observed behavior into the pre-fix source."
        )
        findings = None

        async def finish(args):
            nonlocal findings
            for candidate in args.candidates:
                await sandbox.read_source(candidate.path, 1, 1)
            findings = args
            return {"saved": True}

        await model.loop(
            "Localize this empirically confirmed bug. Inspect actual source before naming files/symbols. "
            "Use up to five ranked candidates; explain the evidence and limitations. Do not claim the future human fix is known.\n"
            + case.spec.model_dump_json()
            + "\nReplay:\n"
            + case.reproduction.model_dump_json(),
            [
                *self.source_tools(sandbox),
                Tool(
                    "finish",
                    "Submit ranked source findings grounded in inspected files.",
                    Findings,
                    finish,
                ),
            ],
            purpose="source localization",
            done=lambda: findings is not None,
            max_turns=12,
        )
        case.findings = findings
        for path in (".github/CODEOWNERS", "CODEOWNERS", "docs/CODEOWNERS"):
            try:
                contents = await sandbox.read_source(path, 1, 200)
                case.owner_evidence.append(
                    f"CODEOWNERS file {path} (rules must be matched to candidate paths):\n{contents}"
                )
                break
            except ValueError:
                continue
        if not case.owner_evidence:
            case.owner_evidence = [
                "No CODEOWNERS found. Depth-one history is insufficient to infer ownership reliably."
            ]
        self.store.save(case, "localization", findings.model_dump())

    async def propose(self, case, sandbox, model):
        self.store.transition(
            case,
            State.PATCH_PROPOSING,
            "Designing a small candidate diff in the disposable repository.",
        )
        proposed = None

        async def apply(args):
            nonlocal proposed
            code, output = await sandbox.exec(
                ["git", "apply", "--check", "-"], input_text=args.diff, check=False
            )
            if code:
                return {
                    "error": output[-4000:],
                    "hint": "Return a valid unified diff with exact context and hunk counts.",
                }
            await sandbox.exec(["git", "apply", "-"], input_text=args.diff)
            await sandbox.exec(["git", "add", "-N", "."])
            _, diff = await sandbox.exec(["git", "diff", "--no-ext-diff", "--binary", "HEAD"])
            if not diff.strip():
                return {"error": "Patch contains no source changes"}
            case.patch_artifact = self.store.artifact(
                case.id, "candidate.patch", diff, "text/x-diff"
            )
            case.patch_rationale = PatchRationale(explanation=args.explanation, risks=args.risks)
            self.store.artifact(
                case.id, "patch-rationale.json", args.model_dump_json(indent=2), "application/json"
            )
            self.store.save(
                case,
                "patch",
                {
                    "artifact": case.patch_artifact,
                    "explanation": args.explanation,
                    "risks": args.risks,
                },
            )
            proposed = args
            return {
                "applied": True,
                "validation": "Build, tests and replay follow. No upstream repository was changed.",
            }

        await model.loop(
            "Propose a minimal causal patch for the confirmed bug. A failing gameplay replay regression already exists. "
            "Explain in plain language what caused the bug, what the changed lines do, why that should fix it, "
            "and what risks or tradeoffs need review. This is a proposed explanation; validation follows. "
            "Inspect exact source lines, then submit a valid unified diff. Do not add diagnostic shortcuts, weaken the oracle, "
            "disable behavior, or change unrelated files. Do not change Gradle, dependencies or build scripts.\n"
            + case.findings.model_dump_json()
            + "\n"
            + case.spec.model_dump_json(),
            [
                *self.source_tools(sandbox),
                Tool(
                    "propose_patch",
                    "Apply a candidate unified diff in this ephemeral repository only.",
                    PatchProposal,
                    apply,
                ),
            ],
            purpose="candidate patch",
            done=lambda: proposed is not None,
            max_turns=10,
        )

    async def validate(self, case, sandbox, model, recorder):
        self.store.transition(
            case,
            State.VALIDATING,
            "Building the candidate and running existing tests, then replaying the original trigger.",
        )
        network = self.settings.validation_network
        await sandbox.start(network=network)
        self.store.save(
            case,
            "validation_environment",
            {
                "network": "bridge" if network else "none",
                "phase": "build and existing tests",
                "worker_image": self.settings.worker_image,
            },
        )
        build = list(sandbox.adapter.build)
        if case.report.game == "mindustry" and not network:
            build.append("--offline")
        code, output = await sandbox.exec(build, timeout=900, check=False)
        artifact = self.store.artifact(case.id, "candidate-build.log", output)
        case.checks.append(
            Check(
                name="Candidate build",
                status="pass" if code == 0 else "fail",
                detail=f"Build exit code {code}",
                artifact=artifact,
            )
        )
        if code:
            case.checks.extend(
                [
                    Check(name=n, status="not_run", detail="Blocked by failed candidate build")
                    for n in ("Existing tests", "Original replay after patch", "Smoke test")
                ]
            )
            self.store.save(case)
            return
        tests = [arg for arg in sandbox.adapter.tests if not (network and arg == "--offline")]
        code, output = await sandbox.exec(tests, timeout=600, check=False)
        artifact = self.store.artifact(case.id, "candidate-tests.log", output)
        case.checks.append(
            Check(
                name="Existing tests",
                status="pass" if code == 0 else "fail",
                detail=f"Test exit code {code}"
                + (
                    ". The log contains UnknownHostException; this worker has networking disabled. Inspect the test log."
                    if code and not network and "UnknownHostException" in output
                    else ""
                ),
                artifact=artifact,
            )
        )
        rep = case.reproduction
        self.store.save(
            case, "validation_environment", {"network": "none", "phase": "fresh game replays"}
        )
        fixed, observed_bugs = 0, 0
        replay_screenshot = None
        for _ in range(self.settings.repetitions):
            verdict, observation = await replay(
                sandbox, recorder, model, rep.steps, rep.oracle, phase="post-patch"
            )
            observed_bugs += int(verdict.observed)
            expected = await model.structured(
                FixedVerdict,
                "Evaluate a candidate fix using this post-replay screenshot. The original symptom was: "
                + rep.oracle.description
                + ". Mark expected_state_reached=true ONLY if this screen shows the exact UI/game state needed to test that symptom. "
                "A different menu, blank screen, loading state or crashed game is inconclusive. "
                "Mark symptom_absent=true ONLY when the correct target state is visible and the reported defect is absent. "
                f"Process state: {observation.get('process')}",
                purpose="post-patch expected-state verification",
                screenshot=observation["screenshot"],
            )
            valid = (
                not verdict.observed
                and expected.expected_state_reached
                and expected.symptom_absent
                and expected.confidence >= 0.8
                and observation.get("process", {}).get("running", False)
            )
            fixed += int(valid)
            replay_screenshot = observation["screenshot_artifact"]
            self.store.save(
                case,
                "validation_replay",
                {
                    "fixed": valid,
                    "expected": expected.model_dump(),
                    "screenshot": observation["screenshot_artifact"],
                },
            )
        case.checks.append(
            Check(
                name="Original replay after patch",
                status="pass" if fixed == self.settings.repetitions else "fail",
                detail=f"{fixed}/{self.settings.repetitions} reached expected state without the symptom; bug seen {observed_bugs} times.",
            )
        )
        # A separate clean launch is a narrow smoke check, not a gameplay coverage claim.
        smoke = recorder.capture(await sandbox.reset(), "smoke")
        running = smoke.get("process", {}).get("running", False)
        case.checks.append(
            Check(
                name="Smoke test",
                status="pass" if running else "fail",
                detail="Clean desktop launch and live process after startup; deeper gameplay smoke coverage is not implemented.",
                artifact=smoke["screenshot_artifact"],
            )
        )
        # Leave the target-state evidence in the viewport; the launch check has its own artifact.
        if replay_screenshot:
            case.latest_screenshot = replay_screenshot
        self.store.save(case)

    @staticmethod
    def report(case: Case) -> str:
        lines = [
            f"# REPRO — {case.report.title}",
            f"\nStatus: **{case.state}**",
            f"\n{case.summary}",
            f"\nGame: {case.report.game} · revision `{case.report.target_commit}`",
            "\n## Player report",
            case.report.body,
        ]
        if case.imported_from:
            lines.insert(
                1,
                f"**Imported recording: {case.imported_from.original_case_id}** · "
                f"Recorded {case.created_at}; imported {case.imported_from.imported_at}.",
            )
        if case.reproduction:
            r = case.reproduction
            lines += [
                "\n## Reproduction",
                f"{r.successful_runs}/{r.total_runs} successful clean replays. "
                f"{r.original_actions} → {len(r.steps)} actions (bounded reduction, not a proof of global minimality).",
            ]
            lines += [
                f"{i + 1}. {a.semantic or a.action} — `{a.model_dump_json()}`"
                for i, a in enumerate(r.steps)
            ]
        if case.findings:
            lines += ["\n## Source findings", case.findings.root_cause]
            lines += [
                f"- `{c.path}` / {c.symbol or 'symbol unknown'} ({c.score:.2f}): {c.reasoning}"
                for c in case.findings.candidates
            ]
            lines += ["\nLimitations: " + "; ".join(case.findings.limitations)]
        if case.checks:
            lines += ["\n## Validation"] + [
                f"- {c.name}: **{c.status}** — {c.detail}" for c in case.checks
            ]
        if case.patch_artifact:
            lines += ["\n## Proposed patch"]
            if case.patch_rationale:
                lines += ["\n### Why this patch should work", case.patch_rationale.explanation]
                lines += ["\n### Risks and tradeoffs"]
                lines += [f"- {risk}" for risk in case.patch_rationale.risks] or [
                    "No specific risks were recorded."
                ]
            else:
                lines += ["No saved explanation is available for this patch."]
        lines += [
            "\n## Usage",
            (
                f"{case.usage.model_calls} model calls; {case.usage.input_tokens} input and {case.usage.output_tokens} output tokens."
                if case.usage
                else "Usage not recorded."
            ),
            "\nCandidate changes exist only in a disposable local repository. Human review does not publish or merge them upstream.",
        ]
        return "\n\n".join(lines) + "\n"
