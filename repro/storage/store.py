from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from pathlib import Path

from repro.models import Case, PatchRationale, State, now


class Store:
    """Durable snapshots and ordered events. One API process owns job execution."""

    def __init__(self, root: Path):
        self.root = root
        root.mkdir(parents=True, exist_ok=True)
        self.database = root / "repro.sqlite3"
        with self.connect() as db:
            db.executescript("""
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS cases (id TEXT PRIMARY KEY, data TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS events (
                    seq INTEGER PRIMARY KEY AUTOINCREMENT, case_id TEXT NOT NULL,
                    created_at TEXT NOT NULL, kind TEXT NOT NULL, data TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS events_case ON events(case_id, seq);
                CREATE TABLE IF NOT EXISTS artifacts (
                    id TEXT PRIMARY KEY, case_id TEXT NOT NULL, name TEXT NOT NULL,
                    sha256 TEXT NOT NULL, size INTEGER NOT NULL, media_type TEXT NOT NULL
                );
            """)

            columns = {row["name"] for row in db.execute("PRAGMA table_info(events)")}
            if "recorded_seq" not in columns:
                db.execute("ALTER TABLE events ADD COLUMN recorded_seq INTEGER")

    def connect(self):
        db = sqlite3.connect(self.database, timeout=15)
        db.row_factory = sqlite3.Row
        return db

    def save(self, case: Case, kind: str | None = None, data: dict | None = None):
        case.updated_at = now()
        with self.connect() as db:
            db.execute(
                "INSERT OR REPLACE INTO cases VALUES (?,?)", (case.id, case.model_dump_json())
            )
            if kind:
                db.execute(
                    "INSERT INTO events(case_id,created_at,kind,data) VALUES (?,?,?,?)",
                    (
                        case.id,
                        now(),
                        kind,
                        json.dumps(data or {"state": case.state, "summary": case.summary}),
                    ),
                )

    def get(self, case_id: str) -> Case:
        with self.connect() as db:
            row = db.execute("SELECT data FROM cases WHERE id=?", (case_id,)).fetchone()
        if not row:
            raise KeyError(case_id)
        case = Case.model_validate_json(row["data"])
        if case.patch_artifact and not case.patch_rationale:
            # Older cases already saved the explanation in their patch event.
            # Match this exact patch, rather than an unrelated later proposal/upload.
            with self.connect() as db:
                rows = db.execute(
                    "SELECT data FROM events WHERE case_id=? AND kind='patch' ORDER BY seq DESC",
                    (case_id,),
                )
                for event in rows:
                    data = json.loads(event["data"])
                    if data.get("artifact") == case.patch_artifact and data.get("explanation"):
                        case.patch_rationale = PatchRationale(
                            explanation=data["explanation"], risks=data.get("risks", [])
                        )
                        break
        return case

    def list(self) -> list[Case]:
        with self.connect() as db:
            return [
                Case.model_validate_json(r["data"])
                for r in db.execute("SELECT data FROM cases ORDER BY rowid DESC")
            ]

    def events(self, case_id: str, after: int = 0) -> list[dict]:
        with self.connect() as db:
            rows = db.execute(
                "SELECT * FROM events WHERE case_id=? AND seq>? ORDER BY seq LIMIT 500",
                (case_id, after),
            )
            return [{**dict(r), "data": json.loads(r["data"])} for r in rows]

    def transition(self, case: Case, state: State, summary: str):
        case.state, case.summary = state, summary
        self.save(case, "state")

    def event(self, case_id: str, seq: int) -> dict:
        with self.connect() as db:
            row = db.execute(
                "SELECT * FROM events WHERE case_id=? AND seq=?", (case_id, seq)
            ).fetchone()
        if not row:
            raise KeyError(seq)
        return {**dict(row), "data": json.loads(row["data"])}

    def latest_events(self, case_id: str, count=100) -> list[dict]:
        with self.connect() as db:
            rows = db.execute(
                "SELECT * FROM events WHERE case_id=? ORDER BY seq DESC LIMIT ?",
                (case_id, min(max(count, 1), 500)),
            ).fetchall()
        return [{**dict(r), "data": json.loads(r["data"])} for r in reversed(rows)]

    def workspace(self, case_id: str) -> Path:
        if not re.fullmatch(r"[a-zA-Z0-9_-]{1,80}", case_id):
            raise ValueError("Invalid case id")
        path = self.root / "cases" / case_id
        path.mkdir(parents=True, exist_ok=True)
        return path

    def artifact(
        self, case_id: str, name: str, content: bytes | str, media_type="text/plain"
    ) -> str:
        name = Path(name).name
        raw = content.encode() if isinstance(content, str) else content
        digest = hashlib.sha256(raw).hexdigest()
        artifact_id = f"{case_id}-{digest[:20]}-{name}"
        path = self.workspace(case_id) / "artifacts" / artifact_id
        path.parent.mkdir(exist_ok=True)
        path.write_bytes(raw)
        with self.connect() as db:
            db.execute(
                "INSERT OR IGNORE INTO artifacts VALUES (?,?,?,?,?,?)",
                (artifact_id, case_id, name, digest, len(raw), media_type),
            )
        return artifact_id

    def artifacts(self, case_id: str) -> list[dict]:
        with self.connect() as db:
            return [
                dict(r)
                for r in db.execute(
                    "SELECT * FROM artifacts WHERE case_id=? ORDER BY rowid DESC", (case_id,)
                )
            ]

    def artifact_path(self, case_id: str, artifact_id: str) -> tuple[Path, str]:
        with self.connect() as db:
            row = db.execute(
                "SELECT * FROM artifacts WHERE id=? AND case_id=?", (artifact_id, case_id)
            ).fetchone()
        if not row:
            raise KeyError(artifact_id)
        return self.workspace(case_id) / "artifacts" / row["id"], row["media_type"]
