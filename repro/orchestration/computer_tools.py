"""Short desktop sequences keep each ordinary action replayable and observable."""

import time
from collections.abc import Awaitable, Callable

from pydantic import BaseModel, Field, model_validator

from repro.agents.openai import Tool
from repro.computer.recorder import Recorder
from repro.models import Action


class ActionSequence(BaseModel):
    actions: list[Action] = Field(min_length=2, max_length=8)

    @model_validator(mode="after")
    def short_sequence(self):
        programmed_seconds = sum(
            action.seconds
            + action.hold_seconds
            + (len(action.text) * 0.01 if action.action == "type" else 0)
            + (abs(action.scroll_y) * 0.12 if action.action == "scroll" else 0)
            for action in self.actions
        )
        if programmed_seconds > 20:
            raise ValueError("A sequence allows at most 20 seconds of waits, holds, typing and scrolling")
        return self


def sequence_tool(
    recorder: Recorder,
    computer: Callable[[Action], Awaitable[dict]],
    remaining_actions: Callable[[], int],
    *,
    phase: str,
) -> Tool:
    async def execute(args: ActionSequence):
        if len(args.actions) > remaining_actions():
            raise ValueError("The complete sequence exceeds the remaining action budget")
        labels = [action.checkpoint for action in args.actions if action.checkpoint]
        if len(set(labels)) != len(labels) or set(labels).intersection(recorder.checkpoints):
            raise ValueError("Sequence checkpoint labels must be new and distinct")

        started = time.monotonic()
        completed = []
        reason = "input_error"
        try:
            observation = await recorder.observe()
            reason = "game_not_running"
            for action in args.actions:
                if not observation.get("process", {}).get("running", False):
                    break
                reason = "input_error"
                observation = await computer(action)
                completed.append(
                    {
                        "index": len(recorder.attempt_actions),
                        "semantic": action.semantic,
                        "checkpoint": action.checkpoint,
                        "screenshot_artifact": observation["screenshot_artifact"],
                        "process": observation.get("process"),
                    }
                )
                reason = (
                    "completed"
                    if observation.get("process", {}).get("running", False)
                    else "game_not_running"
                )
            return {
                **observation,
                "sequence": {
                    "requested": len(args.actions),
                    "executed": len(completed),
                    "stop_reason": reason,
                    "steps": completed,
                },
            }
        finally:
            recorder.store.save(
                recorder.case,
                "action_sequence",
                {
                    "phase": phase,
                    "requested": len(args.actions),
                    "executed": len(completed),
                    "stop_reason": reason,
                    "elapsed_seconds": time.monotonic() - started,
                    "steps": completed,
                    "summary": f"Executed {len(completed)}/{len(args.actions)} sequence actions; {reason}.",
                },
            )

    return Tool(
        "computer_sequence",
        "Execute 2–8 known desktop actions in order without intervening model turns. "
        "Use only when the next inputs do not depend on inspecting an intermediate screen; "
        "use computer for uncertain navigation. Each action keeps its normal wait, hold, "
        "screenshot, checkpoint and replay record. This is not simultaneous or frame-exact. "
        "The final screen and intermediate artifact references are returned. Stops if the "
        "game exits or an input fails. The whole sequence must fit the action budget, use "
        "new distinct checkpoint labels and total at most 20 seconds of waits, holds, typing "
        "and paced scrolling.",
        ActionSequence,
        execute,
    )
