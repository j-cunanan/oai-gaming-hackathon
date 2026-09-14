import base64
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from pydantic import ValidationError

from repro.computer.recorder import Recorder
from repro.models import Action, Case, CaseInput
from repro.orchestration.computer_tools import ActionSequence, sequence_tool
from repro.storage.store import Store


def observation(number, *, running=True):
    return {
        "screenshot": base64.b64encode(f"recorded screen {number}".encode()).decode(),
        "process": {"running": running},
        "logs": f"log {number}",
    }


def setup(tmp_path, observations, *, running=True, remaining=20):
    case = Case(
        report=CaseInput(title="Transport", body="A unit is lost", target_commit="a" * 40)
    )
    store = Store(tmp_path)
    sandbox = SimpleNamespace(
        observe=AsyncMock(return_value=observation(0, running=running)),
        action=AsyncMock(side_effect=observations),
    )
    recorder = Recorder(store, case, sandbox)
    replay_steps = []

    async def computer(action):
        result = await recorder.act(action)
        replay_steps.append(action)
        return result

    tool = sequence_tool(
        recorder, computer, lambda: remaining - len(replay_steps), phase="investigation"
    )
    return recorder, sandbox, replay_steps, tool


async def test_sequence_retains_every_replay_step_checkpoint_image_and_log(tmp_path):
    recorder, sandbox, replay_steps, tool = setup(
        tmp_path, [observation(1), observation(2), observation(3)]
    )
    actions = [
        Action(action="keypress", keys=["space"], seconds=0, checkpoint="before-entry"),
        Action(action="keypress", keys=["d"], hold_seconds=0.4, checkpoint="on-conveyor"),
        Action(action="wait", seconds=1, checkpoint="after-output"),
    ]
    result = await tool.handler(ActionSequence(actions=actions))
    assert replay_steps == actions == recorder.attempt_actions
    assert sandbox.action.await_count == 3
    assert list(recorder.checkpoints) == [a.checkpoint for a in actions]
    assert result["sequence"]["executed"] == 3
    assert result["sequence"]["stop_reason"] == "completed"
    events = recorder.store.events(recorder.case.id)
    recorded = [e["data"] for e in events if e["kind"] == "action"]
    assert [e["action"] for e in recorded] == [a.model_dump() for a in actions]
    assert [e["index"] for e in recorded] == [1, 2, 3]
    for number, event in enumerate(recorded, 1):
        image, _ = recorder.store.artifact_path(recorder.case.id, event["screenshot_after"])
        assert image.read_bytes() == f"recorded screen {number}".encode()
        assert recorder.store.artifact_path(recorder.case.id, event["log_artifact"])[0].exists()
    # Preparing the model's next tool response must not consume retained checkpoint images.
    result.pop("screenshot")
    assert all("screenshot" in item["observation"] for item in recorder.checkpoints.values())


@pytest.mark.parametrize("initially_running", [True, False])
async def test_sequence_never_sends_remaining_inputs_after_game_exit(tmp_path, initially_running):
    recorder, sandbox, replay_steps, tool = setup(
        tmp_path, [observation(1, running=False)], running=initially_running
    )
    actions = [Action(action="keypress", keys=["enter"]), Action(action="type", text="later")]
    result = await tool.handler(ActionSequence(actions=actions))
    count = int(initially_running)
    assert sandbox.action.await_count == count
    assert replay_steps == actions[:count]
    assert result["sequence"]["executed"] == count
    assert result["sequence"]["stop_reason"] == "game_not_running"
    audit = recorder.store.events(recorder.case.id)[-1]
    assert audit["kind"] == "action_sequence" and audit["data"]["executed"] == count


@pytest.mark.parametrize("invalid", ["budget", "duplicate", "existing"])
async def test_invalid_sequence_is_rejected_before_any_desktop_input(tmp_path, invalid):
    recorder, sandbox, replay_steps, tool = setup(
        tmp_path, [], remaining=1 if invalid == "budget" else 20
    )
    if invalid == "existing":
        recorder.checkpoints["second"] = {"index": 1}
    actions = [
        Action(action="wait", checkpoint="second" if invalid == "duplicate" else "first"),
        Action(action="wait", checkpoint="second"),
    ]
    with pytest.raises(ValueError):
        await tool.handler(ActionSequence(actions=actions))
    sandbox.action.assert_not_awaited()
    sandbox.observe.assert_not_awaited()
    assert not replay_steps


async def test_input_failure_keeps_completed_evidence_and_does_not_send_later_actions(tmp_path):
    recorder, sandbox, replay_steps, tool = setup(
        tmp_path, [observation(1), ValueError("Input rejected")]
    )
    actions = [Action(action="wait", checkpoint=f"step-{i}") for i in range(3)]
    with pytest.raises(ValueError, match="Input rejected"):
        await tool.handler(ActionSequence(actions=actions))
    assert sandbox.action.await_count == 2
    assert replay_steps == actions[:1]
    assert list(recorder.checkpoints) == ["step-0"]
    audit = recorder.store.events(recorder.case.id)[-1]["data"]
    assert audit["executed"] == 1 and audit["stop_reason"] == "input_error"


@pytest.mark.parametrize(
    "actions",
    [
        [Action(action="wait")],
        [Action(action="wait")] * 9,
        [Action(action="keypress", keys=["w"], seconds=10, hold_seconds=10)] * 2,
        [Action(action="type", text="x" * 1100)] * 2,
    ],
)
def test_sequence_limits_cover_count_waits_holds_and_typing(actions):
    with pytest.raises(ValidationError):
        ActionSequence(actions=actions)
