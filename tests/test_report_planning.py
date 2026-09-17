import asyncio
import json
from types import SimpleNamespace

import httpx
import openai
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from repro import report_planning
from repro.api import create_app
from repro.config import Settings
from repro.report_planning import PlanRequest, PlanResult, ReportPlan


def plan():
    return ReportPlan(
        title="Test deletion across save and reopen",
        reported_failure="A deleted patch returns.",
        expected_behavior="The entry stays deleted.",
        hypothesis_to_test="The deletion may not persist after saving.",
        steps=[
            {
                "title": title,
                "kind": kind,
                "action": action,
                "evidence_needed": evidence,
            }
            for title, kind, action, evidence in [
                ("Establish state", "setup", "Open the map.", "Record the map and entry."),
                ("Delete and save", "action", "Delete, then save.", "Capture save confirmation."),
                ("Reopen", "checkpoint", "Reopen the same map.", "Record the entry list."),
            ]
        ],
        missing_details=["Which build is affected?"],
        assumptions=[],
        failure_evidence="The entry returns after a confirmed save and reopen.",
        success_evidence="The entry remains absent after the same actions.",
        related_recordings=[{"id": "datapatch", "reason": "Same reported persistence symptom."}],
    )


def settings(tmp_path, key="test-key"):
    return Settings(_env_file=None, data_dir=tmp_path, OPENAI_API_KEY=key)


def request():
    return PlanRequest(report="I delete a data patch, save and reopen the map, and it returns.")


def result():
    return PlanResult(
        id="plan-test",
        created_at="2026-09-17T04:00:00Z",
        model="gpt-5.6-terra",
        elapsed_seconds=1,
        input_tokens=100,
        output_tokens=100,
        report_sha256="a" * 64,
        plan=plan(),
    )


async def test_live_plan_uses_report_only_context_and_retains_provenance(tmp_path, monkeypatch):
    calls = []

    class Client:
        def __init__(self, **kwargs):
            assert kwargs["max_retries"] == 0
            assert kwargs["timeout"] == 45
            self.responses = self

        async def __aenter__(self):
            return self

        async def __aexit__(self, *_):
            pass

        async def parse(self, **kwargs):
            calls.append(kwargs)
            return SimpleNamespace(
                status="completed",
                output_parsed=plan(),
                model="gpt-5.6-terra",
                usage=SimpleNamespace(input_tokens=123, output_tokens=456),
            )

    monkeypatch.setattr(report_planning, "AsyncOpenAI", Client)
    answer = await report_planning.generate_report_plan(settings(tmp_path), request())
    assert len(calls) == 1
    assert calls[0]["store"] is False
    assert "tools" not in calls[0]
    assert calls[0]["text_format"] is ReportPlan
    assert calls[0]["input"][1]["content"] == request().model_dump_json()
    for description in report_planning.recording_descriptions():
        assert set(description) == {"id", "title", "summary", "sampleReport"}
    assert answer.executed is False
    assert answer.input_tokens == 123
    saved = json.loads((tmp_path / "report-plans" / f"{answer.id}.json").read_text())
    assert saved["request"]["report"] == request().report
    assert saved["result"]["report_sha256"] == answer.report_sha256
    assert not (tmp_path / "workspaces").exists()


@pytest.mark.parametrize("status,parsed", [("incomplete", plan()), ("completed", None)])
async def test_incomplete_or_refused_plan_never_becomes_a_result(
    tmp_path, monkeypatch, status, parsed
):
    class Client:
        def __init__(self, **_):
            self.responses = self

        async def __aenter__(self):
            return self

        async def __aexit__(self, *_):
            pass

        async def parse(self, **_):
            return SimpleNamespace(status=status, output_parsed=parsed)

    monkeypatch.setattr(report_planning, "AsyncOpenAI", Client)
    with pytest.raises(ValueError, match="No complete plan"):
        await report_planning.generate_report_plan(settings(tmp_path), request())
    assert not (tmp_path / "report-plans").exists()


def test_planner_input_and_schema_reject_invalid_or_executed_results():
    for data in [
        {"report": " " * 20},
        {"report": "x" * 8001},
        {"report": "valid report text", "game": "luanti"},
    ]:
        with pytest.raises(ValidationError):
            PlanRequest(**data)
    with pytest.raises(ValidationError):
        PlanResult(**{**result().model_dump(), "executed": True})
    with pytest.raises(ValidationError):
        ReportPlan(
            **{
                **plan().model_dump(),
                "related_recordings": [
                    {"id": "datapatch", "reason": "one"},
                    {"id": "datapatch", "reason": "two"},
                ],
            }
        )


def test_planning_endpoint_rejects_missing_key_and_cross_origin(tmp_path):
    with TestClient(create_app(settings(tmp_path, ""))) as client:
        assert client.post("/api/report-plan", json=request().model_dump()).status_code == 503
        assert (
            client.post(
                "/api/report-plan",
                json=request().model_dump(),
                headers={"Origin": "https://example.com"},
            ).status_code
            == 403
        )
        assert client.get("/api/cases").json() == []


async def test_planning_is_single_flight_and_failure_releases_slot(tmp_path, monkeypatch):
    entered, release = asyncio.Event(), asyncio.Event()
    calls = 0

    async def generate(*_):
        nonlocal calls
        calls += 1
        if calls == 1:
            entered.set()
            await release.wait()
            raise TimeoutError()
        return result()

    monkeypatch.setattr("repro.api.generate_report_plan", generate)
    app = create_app(settings(tmp_path))
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        first = asyncio.create_task(client.post("/api/report-plan", json=request().model_dump()))
        await entered.wait()
        assert (
            await client.post("/api/report-plan", json=request().model_dump())
        ).status_code == 409
        release.set()
        response = await first
        assert response.status_code == 503
        assert "test-key" not in response.text
        assert (
            await client.post("/api/report-plan", json=request().model_dump())
        ).status_code == 200
        assert (await client.get("/api/cases")).json() == []


@pytest.mark.parametrize(
    "kind,http_status,expected",
    [
        ("dns", 503, "DNS lookup failed"),
        ("connection", 503, "could not connect"),
        ("timeout", 503, "timed out"),
        ("deadline", 503, "timed out"),
        ("authentication", 503, "rejected the configured API key"),
        ("permission", 503, "denied access"),
        ("quota", 503, "no available quota"),
        ("rate_limit", 429, "rate-limited"),
        ("upstream", 503, "service error"),
        ("request", 502, "rejected the planning request"),
        ("invalid_response", 502, "complete valid plan"),
    ],
)
def test_planner_errors_are_actionable_without_leaking_provider_data(
    tmp_path, monkeypatch, caplog, kind, http_status, expected
):
    provider_request = httpx.Request("POST", "https://api.openai.com/v1/responses")
    private = "private-player-report fake-api-credential"
    if kind in {"dns", "connection"}:
        error = openai.APIConnectionError(message=private, request=provider_request)
        if kind == "dns":
            # httpx/httpcore can wrap the DNS failure before it reaches the SDK.
            error.__cause__ = httpx.ConnectError(
                "[Errno 8] nodename nor servname provided, or not known"
            )
    elif kind == "timeout":
        error = openai.APITimeoutError(request=provider_request)
    elif kind == "deadline":
        error = TimeoutError(private)
    elif kind == "invalid_response":
        error = ValueError(private)
    else:
        upstream_status = {
            "authentication": 401,
            "permission": 403,
            "quota": 429,
            "rate_limit": 429,
            "upstream": 503,
            "request": 400,
        }[kind]
        error = openai.APIStatusError(
            private,
            response=httpx.Response(upstream_status, request=provider_request),
            body={"message": private, "code": "insufficient_quota" if kind == "quota" else None},
        )

    async def generate(*_):
        raise error

    monkeypatch.setattr("repro.api.generate_report_plan", generate)
    with TestClient(create_app(settings(tmp_path))) as client:
        response = client.post("/api/report-plan", json=request().model_dump())
        assert response.status_code == http_status
        assert expected in response.json()["detail"]
        assert "No game actions were executed" in response.json()["detail"]
        assert "report_plan_failed code=" in caplog.text
        assert private not in response.text + caplog.text
        assert client.get("/api/cases").json() == []
