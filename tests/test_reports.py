from io import BytesIO

from fastapi.testclient import TestClient
from pypdf import PdfReader

from repro.api import create_app
from repro.config import Settings
from repro.models import Case, CaseInput, Check, PatchRationale
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
