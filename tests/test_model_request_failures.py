import base64
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock

import httpx
import pytest
from openai import AsyncOpenAI
from pydantic import BaseModel

from repro.agents.openai import Model
from repro.config import Settings
from repro.models import Action, BugSpec, Case, CaseInput, OracleSpec
from repro.orchestration.manager import InvestigationResult, Manager
from repro.storage.store import Store


class Answer(BaseModel):
    summary: str


@pytest.mark.parametrize("entrypoint", ["structured", "loop"])
async def test_sdk_timeout_is_not_retried_or_counted_as_returned_usage(
    tmp_path, monkeypatch, entrypoint
):
    requests = []

    def timeout(request):
        requests.append(request.url)
        raise httpx.ReadTimeout("Simulated slow response", request=request)

    def client(**kwargs):
        return AsyncOpenAI(
            **kwargs, http_client=httpx.AsyncClient(transport=httpx.MockTransport(timeout))
        )

    monkeypatch.setattr("repro.agents.openai.AsyncOpenAI", client)
    settings = Settings(_env_file=None, data_dir=tmp_path, openai_api_key="test-credential")
    store = Store(tmp_path)
    case = Case(report=CaseInput(title="Bug", body="A unit is lost", target_commit="a" * 40))
    model = Model(settings, store, case)
    try:
        with pytest.raises(RuntimeError, match="APITimeoutError"):
            if entrypoint == "structured":
                await model.structured(Answer, "Check the evidence", purpose="verification")
            else:
                await model.loop("Inspect the game", [], purpose="investigation", done=lambda: False)
    finally:
        await model.close()
    assert len(requests) == 1
    assert case.usage.model_calls == case.usage.input_tokens == case.usage.output_tokens == 0
    event = store.events(case.id)[-1]
    assert event["kind"] == "model_request_failed"
    assert event["data"]["error_type"] == "APITimeoutError"
    assert event["data"]["automatic_retries"] == 0 and event["data"]["usage_unavailable"]
    assert "test-credential" not in json.dumps(event)


async def test_verifier_failure_keeps_the_ai_proposal_without_claiming_reproduction(
    tmp_path, monkeypatch
):
    settings = Settings(_env_file=None, data_dir=tmp_path)
    store = Store(tmp_path)
    case = Case(
        report=CaseInput(title="Transport", body="A unit is lost", target_commit="a" * 40),
        spec=BugSpec(
            summary="Reported unit loss",
            bug_class="gameplay",
            observed_behavior="Unit disappears while entering transport",
            expected_behavior="Unit survives transport",
            known_preconditions=[],
            uncertain_conditions=[],
            reproduction_hints=[],
            required_artifacts=[],
            severity="high",
            confidence=1,
        ),
    )
    root = tmp_path / "sandbox"
    (root / "repo/.git").mkdir(parents=True)
    (root / "prepared.json").touch()

    def screen(label):
        return {
            "screenshot": base64.b64encode(label.encode()).decode(),
            "process": {"running": True},
            "logs": "",
        }

    sandbox = SimpleNamespace(
        root=root,
        repo=root / "repo",
        case=case,
        reset=AsyncMock(return_value=screen("initial")),
        observe=AsyncMock(return_value=screen("final")),
        action=AsyncMock(side_effect=lambda action: screen(action.checkpoint)),
    )
    actions = [Action(action="wait", checkpoint=label) for label in ["before", "after"]]

    async def loop(prompt, tools, **kwargs):
        registry = {tool.name: tool.handler for tool in tools}
        for action in actions:
            await registry["computer"](action)
        await registry["finish"](
            InvestigationResult(
                outcome="observed",
                summary="A proposed observation awaiting verification",
                oracle=OracleSpec(
                    kind="sequence", description="Untrusted description", checkpoints=["before", "after"]
                ),
                limitations=[],
            )
        )

    verifier = AsyncMock(side_effect=RuntimeError("Verifier response failed"))
    monkeypatch.setattr("repro.orchestration.manager.verify", verifier)
    with pytest.raises(RuntimeError, match="Verifier response failed"):
        await Manager(settings, store)._investigate(
            case, sandbox, SimpleNamespace(loop=loop), started=0
        )
    assert store.get(case.id).reproduction is None
    event = next(e for e in store.events(case.id) if e["kind"] == "investigation_proposal")
    source, _ = store.artifact_path(case.id, event["data"]["artifact"])
    proposal = json.loads(source.read_text())
    assert proposal["status"] == "unverified_proposal"
    assert proposal["steps"] == [action.model_dump(mode="json") for action in actions]
    assert proposal["proposal"]["oracle"]["description"] == case.spec.observed_behavior
    assert proposal["report"] == case.report.model_dump(mode="json")
    for index, label in enumerate(["before", "after"], 1):
        checkpoint = proposal["checkpoints"][label]
        assert checkpoint["index"] == index
        image, _ = store.artifact_path(case.id, checkpoint["screenshot_artifact"])
        assert image.read_bytes() == label.encode()
    verifier.assert_awaited_once()
