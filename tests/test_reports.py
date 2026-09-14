from io import BytesIO

import pytest
from fastapi.testclient import TestClient
from PIL import Image
from pypdf import PdfReader

from repro.api import create_app
from repro.config import Settings
from repro.models import Case, CaseInput, Check, OracleSpec, PatchRationale, Reproduction
from repro.reporting import render_report
from repro.storage.store import Store


def case_input():
    return CaseInput(
        title='Weather <rules> & "controls"',
        body="The <weather> controls appear twice & should appear once.",
        target_commit="a" * 40,
    )


def test_legacy_rationale_is_bound_to_the_selected_patch(tmp_path):
    store = Store(tmp_path)
    case = Case(report=case_input(), patch_artifact="selected.patch")
    store.save(
        case,
        "patch",
        {
            "artifact": "selected.patch",
            "explanation": "Keep one control.",
            "risks": ["Review navigation."],
        },
    )
    store.save(
        case,
        "patch",
        {"artifact": "another.patch", "explanation": "Unrelated explanation", "risks": []},
    )
    loaded = store.get(case.id)
    assert loaded.patch_rationale.explanation == "Keep one control."
    assert loaded.patch_rationale.risks == ["Review navigation."]
    store.save(loaded)
    assert store.get(case.id).patch_rationale == loaded.patch_rationale


def test_report_defaults_to_pdf_preserves_failed_checks_and_offers_markdown(tmp_path):
    settings = Settings(_env_file=None, data_dir=tmp_path, OPENAI_API_KEY="")
    store = Store(tmp_path)
    case = Case(
        report=case_input(),
        patch_rationale=PatchRationale(
            explanation="Remove only the duplicate constructor.",
            risks=["Keep the original entry reachable."],
        ),
    )
    case.patch_artifact = store.artifact(
        case.id,
        "candidate.patch",
        "--- a/a.java\n+++ b/a.java\n@@ -1,2 +1 @@\n keep();\n-remove();\n",
    )
    case.checks = [
        Check(
            name="Existing tests", status="fail", detail="GitHub fixture could not be downloaded."
        )
    ]
    store.save(case)
    with TestClient(create_app(settings)) as client:
        response = client.get(f"/api/cases/{case.id}/report")
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        assert f"repro-report-{case.id}.pdf" in response.headers["content-disposition"]
        reader = PdfReader(BytesIO(response.content))
        assert reader.metadata.title == "REPRO Report"
        text = "\n".join(page.extract_text() for page in reader.pages)
        for expected in (
            "REPRO Report",
            "<weather>",
            "FAIL",
            "GitHub fixture",
            "Remove only the duplicate",
            "Keep the original",
            "remove();",
        ):
            assert expected in text
        assert "All five required checks passed" not in text
        markdown = client.get(f"/api/cases/{case.id}/report?format=markdown")
        assert markdown.headers["content-type"].startswith("text/plain")
        assert "Why this patch should work" in markdown.text
        assert client.get("/api/cases/missing/report").status_code == 404
        assert client.get(f"/api/cases/{case.id}/report?format=html").status_code == 422
    assert store.get(case.id).usage.model_calls == 0


def test_long_report_paginates_without_reading_another_cases_artifact(tmp_path):
    store = Store(tmp_path)
    owner = Case(report=case_input())
    secret = store.artifact(owner.id, "candidate.patch", "OTHER_CASE_PRIVATE_CONTENT")
    case = Case(report=case_input(), patch_artifact=secret)
    case.report.body = "A long player observation with <markup> & ordinary punctuation. " * 180
    store.save(case)
    reader = PdfReader(BytesIO(render_report(case, store)))
    assert len(reader.pages) > 1
    text = "\n".join(page.extract_text() for page in reader.pages)
    assert "OTHER_CASE_PRIVATE_CONTENT" not in text
    assert "patch file is unavailable" in text
    assert "No saved explanation" in text
    for i, page in enumerate(reader.pages, 1):
        assert f"Page {i}" in page.extract_text()


def test_pdf_includes_stage_times_and_branded_header(tmp_path):
    store = Store(tmp_path)
    case = Case(report=case_input())
    store.save(case, "stage_started", {"stage": "reduce", "summary": "Starting a shorter replay"})
    store.save(case, "minimization", {"original": 23, "reduced": 8})
    with store.connect() as db:
        db.execute(
            "UPDATE events SET created_at='2026-09-13T17:23:01+00:00' WHERE case_id=?", (case.id,)
        )
    reader = PdfReader(BytesIO(render_report(case, store)))
    text = "\n".join(page.extract_text() for page in reader.pages)
    for expected in (
        "REPRO LAB / ENGINEERING REPORT",
        "Investigation timeline",
        "13 Sep 2026 17:23:01",
        "UTC",
        "Starting a shorter replay",
        "23 to 8",
        "No recorded activity",
    ):
        assert expected in text


@pytest.mark.parametrize("fresh_candidate", [True, False])
def test_pdf_shows_current_candidate_evidence_and_never_reuses_a_prior_validation(
    tmp_path, fresh_candidate
):
    store = Store(tmp_path)
    case = Case(report=case_input())

    def screenshot(name, color):
        output = BytesIO()
        Image.new("RGB", (32, 18), color).save(output, format="PNG")
        return store.artifact(case.id, name, output.getvalue(), "image/png")

    old = screenshot("old-candidate.png", "red")
    current = screenshot("current-candidate.png", "green")
    smoke = screenshot("startup-smoke.png", "blue")
    baseline = screenshot("baseline.png", "black")
    baseline_log = store.artifact(case.id, "baseline.log", "Recorded crash signature")
    case.reproduction = Reproduction(
        game="mindustry",
        commit=case.report.target_commit,
        steps=[],
        oracle=OracleSpec(
            kind="crash", description="Game crashes", log_pattern="Recorded crash signature"
        ),
        evidence=[baseline, baseline_log],
    )
    store.save(case, "validation_replay", {"fixed": True, "screenshot": old})
    store.save(case, "state", {"state": "VALIDATING", "summary": "A new validation attempt"})
    if fresh_candidate:
        store.save(case, "validation_replay", {"fixed": True, "screenshot": current})
    case.checks = [
        Check(
            name="Original replay after patch",
            status="pass" if fresh_candidate else "fail",
            detail="Recorded result",
        )
    ]
    case.latest_screenshot = smoke
    store.save(case)
    reader = PdfReader(BytesIO(render_report(case, store)))
    text = "\n".join(page.extract_text() for page in reader.pages)
    pixels = [
        image.image.convert("RGB").getpixel((0, 0))
        for page in reader.pages
        for image in page.images
    ]
    assert (255, 0, 0) not in pixels
    assert (0, 0, 0) in pixels
    assert "Baseline replay evidence: screenshot unavailable" not in text
    if fresh_candidate:
        assert "Candidate replay outcome" in text
        assert (0, 128, 0) in pixels and (0, 0, 255) not in pixels
    else:
        assert "Candidate replay outcome" not in text
        assert "Latest recorded game screen" in text
        assert (0, 0, 255) in pixels and (0, 128, 0) not in pixels
