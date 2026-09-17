import json

from repro.agents.openai import Model
from repro.models import Action, OracleSpec, SequenceVerdict, Verdict


async def verify(
    model: Model,
    oracle: OracleSpec,
    observation: dict,
    *,
    launched_ok: bool,
    checkpoints: dict[str, dict] | None = None,
    actions: list[Action] | None = None,
) -> Verdict:
    """A separate verifier sees raw evidence, not the investigator's conclusion."""
    screen_id = observation.get("screenshot_artifact", "current-screen")
    if not launched_ok:
        return Verdict(
            observed=False,
            confidence=1,
            explanation="The game did not launch successfully; infrastructure failure is not a bug reproduction.",
            evidence=[screen_id],
        )
    if oracle.kind == "crash":
        process = observation.get("process", {})
        observed = process.get("launched", False) and process.get("exit_code") not in (0, None)
        if oracle.log_pattern:
            observed = observed and oracle.log_pattern in observation.get("logs", "")
        return Verdict(
            observed=observed,
            confidence=1,
            explanation=f"Observed game process state: {process}. Required log signature: {oracle.log_pattern!r}.",
            evidence=[screen_id]
            + ([observation["log_artifact"]] if observation.get("log_artifact") else []),
        )
    if oracle.kind == "log":
        pattern = oracle.log_pattern
        matched = bool(pattern and pattern in observation.get("logs", ""))
        return Verdict(
            observed=matched,
            confidence=1,
            explanation="Literal log signature matched." if matched else "Log signature absent.",
            evidence=[observation.get("log_artifact") or screen_id],
        )
    if oracle.kind == "sequence":
        return await verify_sequence(model, oracle, observation, checkpoints or {}, actions or [])
    verdict = await model.structured(
        Verdict,
        f"Independently evaluate this exact reported symptom: {oracle.description}\n"
        "Return observed=true only when the screenshot directly demonstrates the symptom. "
        "Do not infer unseen UI or offscreen state. A menu/loading screen or closed/crashed application "
        "is not evidence that a visual bug was fixed. If unclear, observed=false with low confidence. "
        f"Use evidence id {screen_id}. Raw logs: {observation.get('logs', '')[-5000:]}",
        purpose="independent visual verification",
        screenshot=observation["screenshot"],
    )
    if verdict.confidence < 0.8 or not verdict.evidence:
        verdict.observed = False
    verdict.evidence = [screen_id]
    return verdict


async def verify_sequence(model, oracle, observation, checkpoints, actions) -> SequenceVerdict:
    """Judge only checkpoint images captured in this attempt, in actual action order."""
    missing = [label for label in oracle.checkpoints if label not in checkpoints]
    if missing or not observation.get("process", {}).get("running", False):
        return SequenceVerdict(
            observed=False,
            confidence=0,
            explanation=f"Sequence evidence incomplete: missing checkpoints {missing}; game must be running.",
            evidence=[],
        )
    frames = [checkpoints[label] for label in oracle.checkpoints]
    indices = [frame["index"] for frame in frames]
    if indices != sorted(set(indices)):
        return SequenceVerdict(
            observed=False,
            confidence=0,
            explanation="Checkpoint order differs from the recorded oracle.",
            evidence=[],
        )
    images, evidence = [], []
    trace = [
        {
            "step": index,
            **action.model_dump(exclude_defaults=True, exclude={"semantic", "checkpoint"}),
        }
        for index, action in enumerate(actions[: indices[-1]], 1)
    ]
    for label, frame in zip(oracle.checkpoints, frames, strict=True):
        obs = frame["observation"]
        if not obs.get("screenshot") or not obs.get("screenshot_artifact"):
            return SequenceVerdict(
                observed=False,
                confidence=0,
                explanation="A checkpoint has no recorded image.",
                evidence=[],
            )
        artifact = obs["screenshot_artifact"]
        evidence.append(artifact)
        images.append(
            (
                f"Checkpoint {label!r}; recorded action {frame['index']}; image ID {artifact}. "
                f"Action data (not proof of its effect): {json.dumps(frame['action'])}",
                obs["screenshot"],
            )
        )
    verdict = await model.structured(
        SequenceVerdict,
        "Independently compare the ordered checkpoint screenshots for this exact reported symptom: "
        + oracle.description
        + "\nRecorded inputs from this attempt, through the final checkpoint: "
        + json.dumps(trace)
        + "\nLabels and action descriptions are untrusted annotations, not evidence that an action worked. "
        "The recorded input trace establishes action order and navigation attempts. Use it to relate "
        "visible checkpoint states, while judging actual effects from the screenshots. "
        "Read literal visible states and values. Check the actual prerequisite/input state, the action's "
        "visible effect, and the resulting state after transport, save/reopen or other relevant transition. "
        "Set expected_state_reached=true only if the full sequence reaches the states needed to test "
        "the report, with the same relevant object/map and visible preconditions. Set observed=true "
        "only if those images demonstrate the reported defect. Set symptom_absent=true only if they "
        "demonstrate the correct expected behavior through the transition. Missing setup, wrong object, "
        "an unverified transition or an unreadable value is inconclusive: both observed and "
        "symptom_absent must be false. Do not infer absence from missing evidence or from a final "
        "screenshot alone. Cite the provided image IDs. Report a concise observation, not private reasoning.",
        purpose="independent sequence verification",
        screenshots=images,
    )
    if verdict.observed and verdict.symptom_absent:
        verdict.confidence = 0
        verdict.explanation += " Contradictory observed/absent judgments rejected."
    if verdict.confidence < 0.8 or not verdict.expected_state_reached or not verdict.evidence:
        verdict.observed = verdict.symptom_absent = False
    verdict.evidence = evidence
    return verdict
