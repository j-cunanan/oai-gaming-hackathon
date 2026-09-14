import asyncio
import json
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, Header, HTTPException, Query, Request, UploadFile
from fastapi.responses import (
    FileResponse,
    JSONResponse,
    PlainTextResponse,
    Response,
    StreamingResponse,
)
from fastapi.staticfiles import StaticFiles

from repro.activity import activity_snapshot
from repro.adapters import ADAPTERS
from repro.config import Settings
from repro.models import ACTIVE_STATES, Case, CaseInput, State, patch_validated
from repro.orchestration.manager import Manager
from repro.reporting import render_report
from repro.storage.store import Store


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()
    store = Store(settings.root)
    manager = Manager(settings, store)
    jobs: dict[str, asyncio.Task] = {}
    slot = asyncio.Semaphore(1)

    @asynccontextmanager
    async def lifespan(app):
        for case in store.list():
            if case.state in ACTIVE_STATES:
                store.transition(
                    case,
                    State.FAILED,
                    "Worker interrupted by application restart. Partial artifacts are retained.",
                )
        yield
        for task in jobs.values():
            task.cancel()
        await asyncio.gather(*jobs.values(), return_exceptions=True)

    app = FastAPI(title="REPRO", version="0.1.0", lifespan=lifespan)
    app.state.store = store
    app.state.jobs = jobs
    app.state.manager = manager

    @app.middleware("http")
    async def local_origin_guard(request: Request, call_next):
        # Loopback service. Browser pages from other origins cannot trigger local jobs.
        origin = request.headers.get("origin")
        allowed = {
            f"http://{host}:{port}" for host in ("localhost", "127.0.0.1") for port in (8000, 5173)
        }
        if request.method not in ("GET", "HEAD", "OPTIONS") and origin and origin not in allowed:
            return JSONResponse({"detail": "Untrusted browser origin"}, status_code=403)
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        return response

    def get_case(case_id):
        try:
            return store.get(case_id)
        except KeyError:
            raise HTTPException(404, "Case not found") from None

    def idle(case_id):
        if get_case(case_id).imported_from:
            raise HTTPException(409, "Imported recordings are read-only. Create a new local case.")
        if case_id in jobs and not jobs[case_id].done():
            raise HTTPException(409, "This case already has an active job")

    def dispatch(case, operation):
        idle(case.id)

        async def job():
            async with slot:
                await operation(case)

        jobs[case.id] = asyncio.create_task(job())
        return {"case_id": case.id, "accepted": True}

    @app.get("/api/health")
    async def health():
        return {
            "status": "ok",
            "model": settings.model,
            "ai_configured": bool(
                settings.openai_api_key and settings.openai_api_key.get_secret_value()
            ),
            "repetitions": settings.repetitions,
            "max_model_calls": settings.max_model_calls,
            "worker_image": settings.worker_image,
            "validation_network": settings.validation_network,
            "active_jobs": [k for k, v in jobs.items() if not v.done()],
        }

    @app.get("/api/adapters")
    async def adapters():
        return [{"id": a.id, "upstream": a.upstream, "status": a.status} for a in ADAPTERS.values()]

    @app.get("/api/cases")
    async def list_cases():
        return store.list()

    @app.post("/api/cases", status_code=201)
    async def create_case(report: CaseInput):
        case = Case(report=report)
        store.save(case, "received")
        return case

    @app.get("/api/cases/{case_id}")
    async def detail(case_id: str):
        return get_case(case_id)

    @app.post("/api/cases/{case_id}/prepare", status_code=202)
    async def prepare(case_id: str):
        case = get_case(case_id)
        if case.patch_artifact:
            raise HTTPException(
                409,
                "This workspace contains a candidate patch. Create a new case for a fresh baseline.",
            )
        return dispatch(case, manager.prepare)

    @app.post("/api/cases/{case_id}/investigate", status_code=202)
    async def investigate(case_id: str):
        case = get_case(case_id)
        if not settings.openai_api_key or not settings.openai_api_key.get_secret_value():
            raise HTTPException(503, "Set OPENAI_API_KEY in the backend .env")
        if case.reproduction or case.patch_artifact:
            raise HTTPException(
                409,
                "This case already has a reproduction. Create a new case for another investigation.",
            )
        return dispatch(case, manager.investigate)

    @app.post("/api/cases/{case_id}/cancel")
    async def cancel(case_id: str):
        case = get_case(case_id)
        task = jobs.get(case_id)
        if task and not task.done():
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)
            # Also handles a job cancelled while waiting for the single worker slot.
            case = get_case(case_id)
            store.transition(case, State.CANCELLED, "Job cancelled. Recorded evidence is retained.")
        return get_case(case_id)

    @app.post("/api/cases/{case_id}/replay", status_code=202)
    async def replay_case(case_id: str):
        case = get_case(case_id)
        if not case.reproduction:
            raise HTTPException(409, "No recorded reproduction")

        async def operation(case):
            try:
                await manager.replay_case(case)
            except Exception as exc:
                store.save(case, "error", {"summary": str(exc) or type(exc).__name__})

        return dispatch(case, operation)

    @app.post("/api/cases/{case_id}/validate", status_code=202)
    async def validate_case(case_id: str):
        case = get_case(case_id)
        if not case.patch_artifact:
            raise HTTPException(409, "No candidate patch")
        return dispatch(case, manager.validate_case)

    @app.post("/api/cases/{case_id}/reduce", status_code=202)
    async def reduce_case(case_id: str):
        case = get_case(case_id)
        if not case.reproduction or not case.reproduction.deterministic:
            raise HTTPException(409, "No confirmed reproduction")
        return dispatch(case, manager.refine_case)

    @app.post("/api/cases/{case_id}/approve")
    async def approve(case_id: str):
        case = get_case(case_id)
        idle(case_id)
        if case.state != State.AWAITING_HUMAN or not case.patch_artifact:
            raise HTTPException(409, "No candidate is awaiting review")
        if not patch_validated(case):
            raise HTTPException(
                409, "All recorded validation gates must pass before marking the candidate approved"
            )
        store.transition(
            case,
            State.COMPLETE,
            "Candidate approved for handoff. Download the patch for a reviewed PR; no upstream push occurred.",
        )
        return case

    @app.post("/api/cases/{case_id}/reject")
    async def reject(case_id: str):
        case = get_case(case_id)
        idle(case_id)
        if case.state != State.AWAITING_HUMAN:
            raise HTTPException(409, "No candidate is awaiting review")
        store.transition(
            case,
            State.COMPLETE,
            "Candidate rejected by reviewer. Evidence and diff retained; no upstream change occurred.",
        )
        return case

    @app.get("/api/cases/{case_id}/events")
    async def events(case_id: str, after: int = 0, tail: int = 0):
        get_case(case_id)
        if tail:
            return store.latest_events(case_id, tail)
        return store.events(case_id, max(0, after))

    @app.get("/api/cases/{case_id}/activity")
    def activity(case_id: str, after: int = Query(default=0, ge=0)):
        get_case(case_id)
        return activity_snapshot(store, case_id, after)

    @app.get("/api/cases/{case_id}/events/{seq}")
    def event_record(case_id: str, seq: int):
        get_case(case_id)
        try:
            return store.event(case_id, seq)
        except KeyError:
            raise HTTPException(404, "Event not found") from None

    @app.get("/api/cases/{case_id}/stream")
    async def stream(
        case_id: str,
        request: Request,
        after: int = 0,
        last_event_id: str | None = Header(default=None),
    ):
        get_case(case_id)
        try:
            cursor = max(0, after, int(last_event_id or 0))
        except ValueError:
            raise HTTPException(400, "Invalid Last-Event-ID") from None

        async def generate():
            nonlocal cursor
            while not await request.is_disconnected():
                rows = store.events(case_id, cursor)
                for row in rows:
                    cursor = row["seq"]
                    yield f"id: {cursor}\nevent: update\ndata: {json.dumps(row)}\n\n"
                if not rows:
                    yield ": keepalive\n\n"
                await asyncio.sleep(1)

        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    @app.get("/api/cases/{case_id}/artifacts")
    async def artifacts(case_id: str):
        get_case(case_id)
        return store.artifacts(case_id)

    @app.post("/api/cases/{case_id}/artifacts", status_code=201)
    async def upload(case_id: str, file: UploadFile):
        get_case(case_id)
        idle(case_id)
        raw = await file.read(20 * 1024 * 1024 + 1)
        await file.close()
        if len(raw) > 20 * 1024 * 1024:
            raise HTTPException(413, "Attachment exceeds 20 MB")
        # Retained for the human/evidence log. Arbitrary uploads are never executed or auto-extracted.
        artifact = store.artifact(
            case_id, file.filename or "attachment", raw, "application/octet-stream"
        )
        return {
            "id": artifact,
            "note": "Retained as evidence. Automatic save installation and video normalization are not implemented yet.",
        }

    @app.get("/api/cases/{case_id}/artifacts/{artifact_id}")
    async def artifact(case_id: str, artifact_id: str):
        get_case(case_id)
        try:
            path, media_type = store.artifact_path(case_id, artifact_id)
        except KeyError:
            raise HTTPException(404, "Artifact not found") from None
        if not path.is_file():
            raise HTTPException(404, "Artifact file is missing")
        return FileResponse(
            path,
            media_type=media_type,
            headers={"Content-Security-Policy": "default-src 'none'; sandbox"},
        )

    @app.get("/api/cases/{case_id}/report")
    def report(case_id: str, format: Literal["pdf", "markdown"] = "pdf"):
        case = get_case(case_id)
        if format == "markdown":
            return PlainTextResponse(manager.report(case))
        # Run in FastAPI's thread pool so PDF layout does not stall live worker events.
        return Response(
            render_report(case, store),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'inline; filename="repro-report-{case.id}.pdf"',
                "Cache-Control": "no-store",
            },
        )

    @app.get("/api/benchmarks")
    async def benchmarks():
        cases = [c for c in store.list() if c.benchmark_id]
        return {
            "attempted": len(cases),
            "confirmed": sum(bool(c.reproduction and c.reproduction.deterministic) for c in cases),
            "validated_patches": sum(patch_validated(c) for c in cases),
            "distinct_cases": len({c.benchmark_id for c in cases}),
            "cases": [
                {"id": c.id, "benchmark_id": c.benchmark_id, "state": c.state} for c in cases
            ],
            "note": "Descriptive run counts only. Precision/recall and localization accuracy require evaluator ground truth; unmeasured values are not invented.",
        }

    dist = Path(__file__).resolve().parent.parent / "apps/web/dist"
    if dist.is_dir():
        app.mount("/", StaticFiles(directory=dist, html=True), name="web")

    return app
