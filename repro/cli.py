import asyncio
from pathlib import Path

import typer
import yaml

from repro.config import Settings
from repro.models import Case, CaseInput
from repro.orchestration.manager import Manager
from repro.storage.store import Store

app = typer.Typer(no_args_is_help=True, help="REPRO: evidence-driven game bug investigation")


def context():
    cfg = Settings()
    return cfg, Store(cfg.root)


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
    case = store.get(case_id)
    if case.patch_artifact:
        raise typer.BadParameter("Create a new case to prepare a fresh baseline after patching")
    asyncio.run(Manager(cfg, store).prepare(case))
    case = store.get(case_id)
    typer.echo(f"{case.state}: {case.summary}")


@app.command()
def investigate(case_id: str):
    """Investigate, verify, reduce, localize and propose a candidate patch."""
    cfg, store = context()
    case = store.get(case_id)
    if case.reproduction or case.patch_artifact:
        raise typer.BadParameter("Create a new case to investigate again from a fresh baseline")
    asyncio.run(Manager(cfg, store).investigate(case))
    result = store.get(case_id)
    typer.echo(f"{result.state}: {result.summary}")


@app.command()
def report(case_id: str, output: Path | None = None):
    """Export the engineering report."""
    cfg, store = context()
    text = Manager(cfg, store).report(store.get(case_id))
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
        Manager(cfg, store).replay_case(store.get(case_id), baseline=not candidate)
    )
    typer.echo(verdict.model_dump_json(indent=2))
    if regression and verdict.observed:
        raise typer.Exit(1)


@app.command()
def validate(case_id: str):
    """Rebuild the candidate and rerun its validation gates offline."""
    cfg, store = context()
    asyncio.run(Manager(cfg, store).validate_case(store.get(case_id)))
    typer.echo(store.get(case_id).model_dump_json(indent=2))


@app.command()
def reduce(case_id: str):
    """Refine a confirmed baseline replay and revalidate an existing candidate if it changes."""
    cfg, store = context()
    asyncio.run(Manager(cfg, store).refine_case(store.get(case_id)))
    result = store.get(case_id)
    typer.echo(f"{result.state}: {result.summary}")


@app.command("import-case")
def import_case(manifest: Path):
    """Import model-visible input fields only from a benchmark manifest."""
    _, store = context()
    data = yaml.safe_load(manifest.read_text())
    case = Case(benchmark_id=data["id"], report=CaseInput.model_validate(data["input"]))
    store.save(case, "received")
    typer.echo(case.id)


if __name__ == "__main__":
    app()
