from repro.agents.oracle import verify
from repro.models import Action, OracleSpec


async def replay(
    sandbox, recorder, model, steps: list[Action], oracle: OracleSpec, *, phase="replay"
):
    recorder.reset_attempt()
    observation = recorder.capture(await sandbox.reset(), f"{phase}-start")
    launched_ok = observation.get("process", {}).get("running", False)
    if launched_ok:
        for action in steps:
            observation = await recorder.act(action, phase=phase)
    verdict = await verify(
        model,
        oracle,
        observation,
        launched_ok=launched_ok,
        checkpoints=recorder.checkpoints,
        actions=recorder.attempt_actions,
    )
    model.store.save(
        model.case,
        "replay",
        {"phase": phase, "actions": len(steps), "verdict": verdict.model_dump()},
    )
    return verdict, observation
