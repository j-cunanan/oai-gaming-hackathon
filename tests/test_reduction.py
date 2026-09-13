from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from repro.config import Settings
from repro.minimization.semantic import ReductionProposal, propose_reduction
from repro.models import Action, Case, CaseInput, OracleSpec, Reproduction, Verdict
from repro.orchestration.manager import Manager
from repro.storage.store import Store


def steps():
    return [Action(action="wait", semantic="Open"), Action(action="wait", semantic="Detour")]


async def test_semantic_proposals_cannot_reorder_duplicate_or_invent_actions():
    for indices in ([1, 0], [0, 0], [-1]):
        with pytest.raises(ValidationError):
            ReductionProposal(keep_indices=indices, explanation="Invalid")

    async def propose(*args, **kwargs):
        return ReductionProposal(keep_indices=[2], explanation="Unrecorded index")

    with pytest.raises(ValueError, match="unrecorded"):
        await propose_reduction(
            SimpleNamespace(structured=propose),
            steps(),
            OracleSpec(kind="visual", description="Duplicate buttons"),
        )


async def test_reduction_keeps_confirmed_original_when_shorter_path_is_flaky(tmp_path, monkeypatch):
    store = Store(tmp_path)
    original = steps()
    case = Case(
        report=CaseInput(
            title="Duplicate controls",
            body="The menu has duplicate buttons.",
            target_commit="a" * 40,
        ),
        reproduction=Reproduction(
            game="mindustry",
            commit="a" * 40,
            steps=original,
            oracle=OracleSpec(kind="visual", description="Duplicate buttons"),
            original_actions=2,
            successful_runs=5,
            total_runs=5,
            deterministic=True,
        ),
    )
    store.save(case)
    phases = []

    async def propose(*args, **kwargs):
        return ReductionProposal(keep_indices=[0], explanation="Drop detour")

    async def replay(sandbox, recorder, model, candidate, oracle, *, phase):
        phases.append(phase)
        observed = candidate == original[:1] and phase == "minimization"
        return Verdict(
            observed=observed, confidence=1, explanation="Test observation", evidence=[]
        ), {}

    monkeypatch.setattr("repro.orchestration.manager.replay", replay)
    model = SimpleNamespace(structured=propose, remaining_calls=25)
    await Manager(Settings(_env_file=None, data_dir=tmp_path), store).reduce_replay(
        case, None, model, None
    )
    assert phases.count("reduced-confirmation") == 5
    assert case.reproduction.steps == original
    assert case.reproduction.successful_runs == 5
    assert store.get(case.id).reproduction.steps == original
