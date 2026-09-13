from repro.agents.openai import Model
from repro.models import OracleSpec, Verdict


async def verify(
    model: Model, oracle: OracleSpec, observation: dict, *, launched_ok: bool
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
        return Verdict(
            observed=observed,
            confidence=1,
            explanation=f"Observed game process state: {process}",
            evidence=[screen_id],
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
