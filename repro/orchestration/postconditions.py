"""Freeze affirmative fix checks separately from the minimal crash/log trigger."""

import hashlib
import json
from typing import Literal

from pydantic import BaseModel

from repro.agents.openai import BudgetExceeded, Tool
from repro.agents.oracle import verify
from repro.models import Action, CandidateVerification, OracleSpec
from repro.orchestration.computer_tools import sequence_tool


class Empty(BaseModel):
    pass


class Conclusion(BaseModel):
    outcome: Literal["verified", "inconclusive"]
    summary: str
    oracle: OracleSpec | None


def trigger_identity(case):
    raw = {
        "report": case.report.model_dump(mode="json"),
        "steps": [step.model_dump(mode="json") for step in case.reproduction.steps],
        "oracle": case.reproduction.oracle.model_dump(mode="json"),
    }
    return hashlib.sha256(json.dumps(raw, sort_keys=True).encode()).hexdigest()


def current_plan(case):
    plan = case.candidate_verification
    return (
        plan
        if plan
        and plan.trigger_sha256 == trigger_identity(case)
        and plan.patch_artifact == case.patch_artifact
        else None
    )


async def plan_postconditions(settings, store, case, sandbox, model, recorder, source_tools):
    """Explore additional candidate actions; exploratory success is never a repeated-run gate."""
    if model.remaining_calls <= settings.repetitions + 2:
        raise BudgetExceeded("Insufficient calls to plan and repeat affirmative fix checks")
    followups, conclusion = [], None

    async def reset(_):
        followups.clear()
        recorder.reset_attempt()
        observation = recorder.capture(await sandbox.reset(), "fix-check-start")
        for action in case.reproduction.steps:
            if not observation.get("process", {}).get("running", False):
                break
            observation = await recorder.act(action, phase="fix-check-setup")
        return observation

    observation = await reset(Empty())
    if not observation.get("process", {}).get("running", False):
        store.save(
            case,
            "fix_check_unavailable",
            {
                "summary": "Candidate stopped during the original trigger; additional fix checks cannot start."
            },
        )
        return None

    async def computer(action):
        if len(followups) >= min(40, settings.max_actions):
            raise ValueError("Additional fix-check action budget exhausted; finish honestly")
        result = await recorder.act(action, phase="fix-check-exploration")
        followups.append(action)
        return result

    async def observe(_):
        return await recorder.observe()

    async def finish(args):
        nonlocal conclusion
        if args.outcome == "inconclusive":
            conclusion = args
            return {"recorded": True}
        if not followups or not args.oracle or args.oracle.kind != "sequence":
            raise ValueError("Save at least one follow-up action and a sequence oracle")
        args.oracle.description = case.reproduction.oracle.description
        observed = await recorder.observe()
        verdict = await verify(
            model,
            args.oracle,
            observed,
            launched_ok=True,
            checkpoints=recorder.checkpoints,
            actions=recorder.attempt_actions,
        )
        store.save(case, "fix_check_experiment", verdict.model_dump())
        if verdict.observed or not verdict.expected_state_reached or not verdict.symptom_absent:
            return {
                "accepted": False,
                "verification": verdict.model_dump(),
                "next_step": "Capture the missing visible prerequisites or postconditions, or finish as inconclusive.",
            }
        conclusion = args
        return {"recorded": True, "next_step": "Fresh repetitions are still required."}

    store.save(
        case,
        "fix_check_started",
        {
            "summary": "Checking affirmative postconditions after the frozen trigger. Exploratory actions do not count as repeated validation."
        },
    )
    await model.loop(
        "The candidate has just executed the original frozen trigger shown below. Verify the full "
        "expected behavior from the report, such as successfully reopening a saved map with its "
        "object retained. Survival alone does not establish a fix. Add only the UI actions needed "
        "to check those postconditions. You cannot edit the trigger or patch. Capture an initial "
        "checkpoint with a labeled wait, then the important transitions and final state, using "
        "neutral distinct labels. Select 2–8 meaningful checkpoints for a sequence oracle. "
        "Each follow-up will later run after the unchanged trigger on fresh profiles. Reset "
        "restores the candidate and executes the trigger again, discarding only this experiment's "
        "follow-ups. A separate verifier must see the expected behavior; do not assume clicks "
        "worked or claim untested save/load behavior. Reloading may change the camera framing; "
        "use normal zoom or a non-modifying picker to identify a retained object when needed. "
        "Focus on visible postconditions and consult source only when it resolves a specific "
        "navigation question. Finish inconclusive if the expected behavior cannot be shown.\n"
        + case.report.model_dump_json()
        + "\nFrozen trigger: "
        + json.dumps([a.model_dump() for a in case.reproduction.steps]),
        [
            Tool(
                "computer",
                "Perform a candidate fix-check action and optionally capture a named checkpoint. seconds is settling time; hold_seconds holds keys or a button; keys on pointer actions are modifiers.",
                Action,
                computer,
            ),
            sequence_tool(
                recorder,
                computer,
                lambda: min(40, settings.max_actions) - len(followups),
                phase="fix-check-exploration",
            ),
            Tool("observe", "Capture the current game screen and process state.", Empty, observe),
            Tool(
                "reset",
                "Restore a fresh candidate profile and replay the unchanged trigger.",
                Empty,
                reset,
            ),
            *source_tools,
            Tool(
                "finish",
                "Propose verified postconditions with selected checkpoints, or record an honest limitation.",
                Conclusion,
                finish,
            ),
        ],
        purpose="candidate verification planning",
        done=lambda: conclusion is not None,
        observation=observation,
        max_turns=min(40, model.remaining_calls - settings.repetitions - 1),
    )
    if conclusion.outcome != "verified":
        store.save(case, "fix_check_unavailable", {"summary": conclusion.summary})
        return None
    plan = case.candidate_verification = CandidateVerification(
        trigger_sha256=trigger_identity(case),
        patch_artifact=case.patch_artifact,
        followup_steps=list(followups),
        oracle=conclusion.oracle,
    )
    artifact = store.artifact(
        case.id, "candidate-verification.json", plan.model_dump_json(indent=2), "application/json"
    )
    store.save(
        case,
        "fix_check_plan",
        {
            "artifact": artifact,
            "summary": f"Frozen {len(followups)} additional fix-check actions. The {len(case.reproduction.steps)}-action trigger is unchanged; fresh repetitions follow.",
        },
    )
    return plan
