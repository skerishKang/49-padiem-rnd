from __future__ import annotations

import logging
import subprocess
import threading
from pathlib import Path
from typing import Any, Sequence

from . import job_manager


LOGGER = logging.getLogger("pipeline.backend")

BASE_DIR = Path(__file__).resolve().parent.parent


def resolve_path(path_str: str) -> Path:
    """프로젝트 루트를 기준으로 경로를 해석."""
    path = Path(path_str)
    if not path.is_absolute():
        path = (BASE_DIR / path).resolve()
    return path


def run_module(command: Sequence[str]) -> dict[str, str]:
    """모듈 실행을 위한 동기 서브프로세스 호출."""
    try:
        result = subprocess.run(
            command,
            check=True,
            cwd=BASE_DIR,
            capture_output=True,
            text=True,
        )
        return {"stdout": result.stdout, "stderr": result.stderr}
    except FileNotFoundError as exc:
        raise RuntimeError("명령 실행 파일을 찾을 수 없습니다.") from exc
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(exc.stderr or "모듈 실행 중 오류 발생") from exc


def start_module_job(command: Sequence[str], meta: dict[str, Any] | None = None) -> str:
    """비동기 작업으로 모듈 실행."""

    job_id = job_manager.create_job(meta)
    command_list = list(command)

    def _worker() -> None:
        LOGGER.info("작업 %s 시작: %s", job_id, " ".join(command_list))
        job_manager.mark_running(job_id)
        try:
            result = run_module(command_list)
        except Exception as exc:  # noqa: BLE001
            LOGGER.exception("작업 %s 실패", job_id)
            job_manager.mark_failed(job_id, str(exc))
            return
        job_manager.mark_success(job_id, result)
        LOGGER.info("작업 %s 완료", job_id)

    thread = threading.Thread(target=_worker, daemon=True)
    thread.start()
    return job_id
