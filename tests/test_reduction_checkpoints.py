from types import SimpleNamespace
from unittest.mock import AsyncMock

from repro.config import Settings
from repro.models import Action, Case, CaseInput, OracleSpec, Reproduction, Verdict
from repro.orchestration.manager import Manager
from repro.storage.store import Store


async def test_incomplete_checkpoint_deletions_never_launch_a_game(tmp_path, monkeypatch):
    store = Store(tmp_path)
    steps = [
        Action(action="wait", checkpoint="before"),
        Action(action="wait"),
        Action(action="wait", checkpoint="after"),
    ]
    case = Case(
        report=CaseInput(
            title="Persistence",
            body="The deletion returns after reopening.",
            target_commit="a" * 40,
        ),
        reproduction=Reproduction(
            game="mindustry",
            commit="a" * 40,
            steps=steps,
            original_actions=3,
            oracle=OracleSpec(
                kind="sequence",
                description="The deletion returns after reopening.",
                checkpoints=["before", "after"],
            ),
            successful_runs=5,
            total_runs=5,
            deterministic=True,
        ),
    )
    monkeypatch.setattr(
        "repro.orchestration.manager.propose_reduction",
        AsyncMock(return_value=(steps[1:], SimpleNamespace(model_dump=lambda: {}))),
    )

    async def replay(sandbox, recorder, model, actions, oracle, **kwargs):
        assert [
            a.checkpoint for a in actions if a.checkpoint in oracle.checkpoints
        ] == oracle.checkpoints
        return Verdict(
            observed=True, confidence=1, explanation="Fresh complete sequence", evidence=["image"]
        ), {}

    replay_mock = AsyncMock(side_effect=replay)
    monkeypatch.setattr("repro.orchestration.manager.replay", replay_mock)
    await Manager(Settings(_env_file=None, repetitions=2), store).reduce_replay(
        case, None, SimpleNamespace(remaining_calls=50), None
    )
    assert replay_mock.await_count >= 2  # Any accepted reduction still needs fresh confirmation.
    skipped = [e for e in store.events(case.id) if e["kind"] == "reduction_trial_skipped"]
    assert skipped
    assert [a.checkpoint for a in case.reproduction.steps if a.checkpoint] == ["before", "after"]
    assert case.reproduction.deterministic
