from __future__ import annotations

import json
import logging
import os
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

logger = logging.getLogger(__name__)
_write_lock = threading.Lock()


DATA_FILES = {
    "resume": "resume_analyses.jsonl",
    "job": "job_analyses.jsonl",
    "fake_job": "fake_job_checks.jsonl",
    "resume_ai": "resume_ai_generations.jsonl",
}


def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _database_dir() -> Path:
    configured = os.getenv("DATABASE_DIR", "").strip()
    if configured:
        raw = Path(configured).expanduser()
        if raw.is_absolute():
            return raw
        return (_project_root() / raw).resolve()
    return Path(__file__).resolve().parent / "db"


def _database_file(kind: str) -> Path:
    filename = DATA_FILES[kind]
    return _database_dir() / filename


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _new_record_id() -> str:
    return uuid4().hex


def init_db() -> None:
    db_dir = _database_dir()
    db_dir.mkdir(parents=True, exist_ok=True)

    for kind in DATA_FILES:
        path = _database_file(kind)
        if not path.exists():
            path.touch()


def db_is_ready() -> bool:
    try:
        init_db()
        for kind in DATA_FILES:
            path = _database_file(kind)
            if not path.exists():
                return False
        return True
    except Exception:
        logger.exception("Database readiness check failed.")
        return False


def _append_json_line(kind: str, payload: dict[str, Any]) -> str | None:
    try:
        init_db()
        record_id = payload.get("id") or _new_record_id()
        payload["id"] = record_id

        with _write_lock:
            with _database_file(kind).open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(payload, ensure_ascii=False) + "\n")
        return str(record_id)
    except Exception:
        logger.exception("Failed to write %s record to JSON database.", kind)
        return None


def _read_json_lines(kind: str, limit: int = 20) -> list[dict[str, Any]]:
    try:
        init_db()
        path = _database_file(kind)
        if not path.exists():
            return []

        records: list[dict[str, Any]] = []
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                row = line.strip()
                if not row:
                    continue
                try:
                    payload = json.loads(row)
                    if isinstance(payload, dict):
                        records.append(payload)
                except json.JSONDecodeError:
                    continue

        records.reverse()
        return records[: max(1, limit)]
    except Exception:
        logger.exception("Failed to read %s records from JSON database.", kind)
        return []


def list_resume_analysis_history(limit: int = 20) -> list[dict[str, Any]]:
    return _read_json_lines("resume", limit=limit)


def save_resume_analysis(
    *,
    source: str,
    resume_filename: str | None,
    parsed_resume: dict[str, Any],
    recommended_jobs: list[dict[str, Any]] | None = None,
) -> str | None:
    record = {
        "id": _new_record_id(),
        "created_at": _utc_now_iso(),
        "source": source,
        "resume_filename": resume_filename,
        "candidate_name": parsed_resume.get("name"),
        "resume_score": parsed_resume.get("resume_score"),
        "payload": {
            "resume": parsed_resume,
            "recommended_jobs": recommended_jobs or [],
        },
    }
    return _append_json_line("resume", record)


def save_job_analysis(
    *,
    source: str,
    job_description: str,
    analysis: dict[str, Any],
    match_result: dict[str, Any] | None = None,
) -> str | None:
    record = {
        "id": _new_record_id(),
        "created_at": _utc_now_iso(),
        "source": source,
        "role_title": analysis.get("role_title"),
        "quality_score": analysis.get("quality_score"),
        "match_score": (match_result or {}).get("match_score"),
        "payload": {
            "job_description": job_description,
            "analysis": analysis,
            "match": match_result or {},
        },
    }
    return _append_json_line("job", record)


def save_fake_job_check(
    *,
    source: str,
    job_url: str | None,
    result: dict[str, Any],
) -> str | None:
    record = {
        "id": _new_record_id(),
        "created_at": _utc_now_iso(),
        "source": source,
        "job_url": job_url,
        "scam_probability": result.get("scam_probability"),
        "risk_level": result.get("risk_level"),
        "payload": result,
    }
    return _append_json_line("fake_job", record)


def save_resume_ai_generation(
    *,
    source: str,
    source_mode: str,
    result: dict[str, Any],
) -> str | None:
    job_target = result.get("job_target") or {}
    record = {
        "id": _new_record_id(),
        "created_at": _utc_now_iso(),
        "source": source,
        "source_mode": source_mode,
        "role_title": job_target.get("role_title"),
        "resume_filename": result.get("resume_filename"),
        "payload": result,
    }
    return _append_json_line("resume_ai", record)
