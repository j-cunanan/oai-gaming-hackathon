import asyncio
from pathlib import Path

import typer
import yaml

from repro.config import Settings
from repro.models import Case, CaseInput
from repro.orchestration.manager import Manager
from repro.reporting import render_report
from repro.storage.store import Store

app = typer.Typer(no_args_is_help=True, help="REPRO: evidence-driven game bug investigation")


def context():
    cfg = Settings()
    return cfg, Store(cfg.root)


def local_case(store: Store, case_id: str) -> Case:
    case = store.get(case_id)
    if case.imported_from:
        raise typer.BadParameter("Imported recordings are read-only. Create a new local case.")
    return case


@app.command()
def serve(host: str = "127.0.0.1", port: int = 8000):
    """Start the API and the built dashboard (one worker process)."""
    import uvicorn

    uvicorn.run(
        "repro.api:create_app", factory=True, host=host, port=port, timeout_graceful_shutdown=5
    )


@app.command()
def ingest(
    report: Path,
    commit: str = typer.Option(..., help="Exact 40-character game revision SHA"),
    game: str = "mindustry",
    title: str = "Player bug report",
):
    """Store a pasted report from a local text file."""
    _, store = context()
    case = Case(
        report=CaseInput(title=title, body=report.read_text(), game=game, target_commit=commit)
    )
    store.save(case, "received")
    typer.echo(case.id)


@app.command()
def prepare(case_id: str):
    """Fetch the exact revision and build it in the preparation sandbox."""
    cfg, store = context()
    case = local_case(store, case_id)
    if case.patch_artifact:
        raise typer.BadParameter("Create a new case to prepare a fresh baseline after patching")
    asyncio.run(Manager(cfg, store).prepare(case))
    case = local_case(store, case_id)
    typer.echo(f"{case.state}: {case.summary}")


@app.command()
def investigate(case_id: str):
    """Investigate, verify, reduce, localize and propose a candidate patch."""
    cfg, store = context()
    case = local_case(store, case_id)
    if case.reproduction or case.patch_artifact:
        raise typer.BadParameter("Create a new case to investigate again from a fresh baseline")
    asyncio.run(Manager(cfg, store).investigate(case))
    result = local_case(store, case_id)
    typer.echo(f"{result.state}: {result.summary}")


@app.command()
def report(case_id: str, output: Path | None = None):
    """Export to .pdf or Markdown; omit --output to print Markdown."""
    cfg, store = context()
    case = store.get(case_id)
    if output and output.suffix.lower() == ".pdf":
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(render_report(case, store))
        typer.echo(str(output))
        return
    text = Manager(cfg, store).report(case)
    if output:
        output.write_text(text)
    else:
        typer.echo(text)


@app.command()
def cases():
    """List persisted cases."""
    _, store = context()
    for case in store.list():
        typer.echo(f"{case.id}  {case.state:26} {case.report.title}")


@app.command()
def replay(case_id: str, candidate: bool = False, regression: bool = False):
    """Replay recorded actions. --regression exits 1 when the bug is observed."""
    cfg, store = context()
    verdict = asyncio.run(
        Manager(cfg, store).replay_case(local_case(store, case_id), baseline=not candidate)
    )
    typer.echo(verdict.model_dump_json(indent=2))
    if regression and verdict.observed:
        raise typer.Exit(1)


@app.command()
def validate(case_id: str):
    """Rebuild and validate; test networking follows REPRO_VALIDATION_NETWORK."""
    cfg, store = context()
    asyncio.run(Manager(cfg, store).validate_case(local_case(store, case_id)))
    typer.echo(local_case(store, case_id).model_dump_json(indent=2))


@app.command()
def reduce(case_id: str):
    """Refine a confirmed baseline replay and revalidate an existing candidate if it changes."""
    cfg, store = context()
    asyncio.run(Manager(cfg, store).refine_case(local_case(store, case_id)))
    result = local_case(store, case_id)
    typer.echo(f"{result.state}: {result.summary}")


@app.command("import-case")
def import_case(manifest: Path):
    """Import model-visible input fields only from a benchmark manifest."""
    _, store = context()
    data = yaml.safe_load(manifest.read_text())
    case = Case(benchmark_id=data["id"], report=CaseInput.model_validate(data["input"]))
    store.save(case, "received")
    typer.echo(case.id)


@app.command("import-evidence")
def import_recording(
    directory: Path,
    case_id: str | None = typer.Option(None, "--id", help="Target imported case id"),
    force: bool = typer.Option(False, help="Replace an existing imported recording"),
):
    """Verify and import a recorded evidence package, preserving its provenance."""
    from repro.storage.evidence import import_evidence

    _, store = context()
    try:
        case = import_evidence(store, directory, case_id=case_id, force=force)
    except (ValueError, OSError, KeyError) as exc:
        raise typer.BadParameter(str(exc)) from exc
    with store.connect() as db:
        count = db.execute("SELECT count(*) FROM events WHERE case_id=?", (case.id,)).fetchone()[0]
    typer.echo(f"Imported recording: {case.id} · {case.state}")
    for check in case.checks:
        typer.echo(f"  {check.name}: {check.status}")
    typer.echo(
        f"{len(case.reproduction.steps) if case.reproduction else 0} actions · "
        f"{len(store.artifacts(case.id))} artifacts · {count} events"
    )


if __name__ == "__main__":
    app()
