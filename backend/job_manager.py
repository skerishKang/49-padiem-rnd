from __future__ import annotations

import threading
import uuid
from datetime import datetime
from typing import Any


class JobStatus:
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"


def _now() -> str:
    return datetime.utcnow().isoformat() + "Z"


_lock = threading.Lock()
_jobs: dict[str, dict[str, Any]] = {}


def create_job(meta: dict[str, Any] | None = None) -> str:
    job_id = uuid.uuid4().hex
    with _lock:
        _jobs[job_id] = {
            "job_id": job_id,
            "status": JobStatus.PENDING,
            "result": None,
            "error": None,
            "created_at": _now(),
            "updated_at": _now(),
            "meta": meta or {},
        }
    return job_id


def mark_running(job_id: str) -> None:
    with _lock:
        if job_id not in _jobs:
            raise KeyError(job_id)
        _jobs[job_id]["status"] = JobStatus.RUNNING
        _jobs[job_id]["updated_at"] = _now()


def mark_success(job_id: str, result: dict[str, Any] | None = None) -> None:
    with _lock:
        if job_id not in _jobs:
            raise KeyError(job_id)
        _jobs[job_id]["status"] = JobStatus.SUCCESS
        _jobs[job_id]["result"] = result or {}
        _jobs[job_id]["error"] = None
        _jobs[job_id]["updated_at"] = _now()


def mark_failed(job_id: str, error: str) -> None:
    with _lock:
        if job_id not in _jobs:
            raise KeyError(job_id)
        _jobs[job_id]["status"] = JobStatus.FAILED
        _jobs[job_id]["error"] = error
        _jobs[job_id]["updated_at"] = _now()


def get_job(job_id: str) -> dict[str, Any]:
    with _lock:
        if job_id not in _jobs:
            raise KeyError(job_id)
        return dict(_jobs[job_id])


def list_jobs() -> list[dict[str, Any]]:
    with _lock:
        return [dict(job) for job in _jobs.values()]
