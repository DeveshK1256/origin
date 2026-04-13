from __future__ import annotations

import json
import logging
import os
import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol
from uuid import uuid4

from supabase import Client, create_client

logger = logging.getLogger(__name__)
_write_lock = threading.Lock()

DATA_FILES = {
    "resume": "resume_analyses.jsonl",
    "job": "job_analyses.jsonl",
    "fake_job": "fake_job_checks.jsonl",
    "resume_ai": "resume_ai_generations.jsonl",
}

SUPABASE_TABLES = {
    "resume": "resume_analyses",
    "job": "job_analyses",
    "fake_job": "fake_job_checks",
    "resume_ai": "resume_ai_generations",
}


class StorageBackend(Protocol):
    def init(self) -> bool:
        ...

    def is_ready(self) -> bool:
        ...

    def append(self, kind: str, payload: dict[str, Any]) -> str | None:
        ...

    def read(self, kind: str, limit: int) -> list[dict[str, Any]]:
        ...


@dataclass
class BackendStatus:
    primary: str
    fallback: str | None = None


_BACKEND: StorageBackend | None = None
_BACKEND_STATUS = BackendStatus(primary="unknown")


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


def _is_truthy(value: str | None, *, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


class LocalJsonStorage:
    def init(self) -> bool:
        db_dir = _database_dir()
        db_dir.mkdir(parents=True, exist_ok=True)

        for kind in DATA_FILES:
            path = _database_file(kind)
            if not path.exists():
                path.touch()
        return True

    def is_ready(self) -> bool:
        try:
            self.init()
            for kind in DATA_FILES:
                path = _database_file(kind)
                if not path.exists():
                    return False
            return True
        except Exception:
            logger.exception("Local database readiness check failed.")
            return False

    def append(self, kind: str, payload: dict[str, Any]) -> str | None:
        try:
            self.init()
            record_id = str(payload.get("id") or _new_record_id())
            payload["id"] = record_id

            with _write_lock:
                with _database_file(kind).open("a", encoding="utf-8") as handle:
                    handle.write(json.dumps(payload, ensure_ascii=False) + "\n")
            return record_id
        except Exception:
            logger.exception("Failed to write %s record to local JSON storage.", kind)
            return None

    def read(self, kind: str, limit: int) -> list[dict[str, Any]]:
        try:
            self.init()
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
            logger.exception("Failed to read %s records from local JSON storage.", kind)
            return []


class SupabaseStorage:
    def __init__(self, url: str, service_key: str):
        self.url = url
        self.service_key = service_key
        self.client: Client = create_client(url, service_key)

    def init(self) -> bool:
        return self.is_ready()

    def is_ready(self) -> bool:
        try:
            # Lightweight readiness check against one known table.
            self.client.table(SUPABASE_TABLES["resume"]).select("id").limit(1).execute()
            return True
        except Exception:
            logger.exception("Supabase readiness check failed.")
            return False

    def append(self, kind: str, payload: dict[str, Any]) -> str | None:
        table = SUPABASE_TABLES[kind]
        record_id = str(payload.get("id") or _new_record_id())
        payload["id"] = record_id
        try:
            self.client.table(table).insert(payload).execute()
            return record_id
        except Exception:
            logger.exception("Failed to insert %s record into Supabase.", kind)
            return None

    def read(self, kind: str, limit: int) -> list[dict[str, Any]]:
        table = SUPABASE_TABLES[kind]
        try:
            response = (
                self.client.table(table)
                .select("*")
                .order("created_at", desc=True)
                .limit(max(1, limit))
                .execute()
            )
            data = getattr(response, "data", None)
            if isinstance(data, list):
                return [item for item in data if isinstance(item, dict)]
            return []
        except Exception:
            logger.exception("Failed to read %s records from Supabase.", kind)
            return []


class HybridStorage:
    """Supabase-first storage with automatic local fallback."""

    def __init__(self, primary: StorageBackend, fallback: StorageBackend):
        self.primary = primary
        self.fallback = fallback

    def init(self) -> bool:
        primary_ready = False
        try:
            primary_ready = self.primary.init()
        except Exception:
            logger.exception("Primary storage init failed.")

        fallback_ready = False
        try:
            fallback_ready = self.fallback.init()
        except Exception:
            logger.exception("Fallback storage init failed.")

        return primary_ready or fallback_ready

    def is_ready(self) -> bool:
        return self.primary.is_ready() or self.fallback.is_ready()

    def append(self, kind: str, payload: dict[str, Any]) -> str | None:
        primary_result = self.primary.append(kind, dict(payload))
        if primary_result:
            return primary_result
        return self.fallback.append(kind, payload)

    def read(self, kind: str, limit: int) -> list[dict[str, Any]]:
        records = self.primary.read(kind, limit)
        if records:
            return records
        return self.fallback.read(kind, limit)


def _build_storage_backend() -> tuple[StorageBackend, BackendStatus]:
    local_backend = LocalJsonStorage()

    backend_mode = os.getenv("DATABASE_BACKEND", "auto").strip().lower()
    supabase_url = os.getenv("SUPABASE_URL", "").strip()
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()

    has_supabase = bool(supabase_url and supabase_key)

    if backend_mode == "local":
        return local_backend, BackendStatus(primary="local")

    if backend_mode == "supabase" and not has_supabase:
        logger.warning(
            "DATABASE_BACKEND=supabase but Supabase credentials are missing. Falling back to local storage."
        )
        return local_backend, BackendStatus(primary="local")

    if has_supabase:
        supabase_backend = SupabaseStorage(supabase_url, supabase_key)

        if _is_truthy(os.getenv("SUPABASE_FALLBACK_LOCAL", "1"), default=True):
            return HybridStorage(supabase_backend, local_backend), BackendStatus(
                primary="supabase",
                fallback="local",
            )

        return supabase_backend, BackendStatus(primary="supabase")

    return local_backend, BackendStatus(primary="local")


def _get_backend() -> StorageBackend:
    global _BACKEND, _BACKEND_STATUS
    if _BACKEND is None:
        _BACKEND, _BACKEND_STATUS = _build_storage_backend()
    return _BACKEND


def storage_status() -> dict[str, Any]:
    _get_backend()
    return {
        "primary": _BACKEND_STATUS.primary,
        "fallback": _BACKEND_STATUS.fallback,
    }


def init_db() -> None:
    backend = _get_backend()
    backend.init()


def db_is_ready() -> bool:
    backend = _get_backend()
    return backend.is_ready()


def _append_record(kind: str, payload: dict[str, Any]) -> str | None:
    backend = _get_backend()
    return backend.append(kind, payload)


def _read_records(kind: str, limit: int = 20) -> list[dict[str, Any]]:
    backend = _get_backend()
    return backend.read(kind, max(1, limit))


def list_resume_analysis_history(limit: int = 20) -> list[dict[str, Any]]:
    return _read_records("resume", limit=limit)


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
    return _append_record("resume", record)


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
    return _append_record("job", record)


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
    return _append_record("fake_job", record)


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
    return _append_record("resume_ai", record)
