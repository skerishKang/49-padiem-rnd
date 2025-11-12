from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from .. import job_manager

router = APIRouter(prefix="/jobs", tags=["Jobs"])


@router.get("/{job_id}")
async def get_job(job_id: str) -> dict:
    """작업 상태 조회."""
    try:
        return job_manager.get_job(job_id)
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"존재하지 않는 작업 ID입니다: {job_id}",
        ) from exc


@router.get("/")
async def list_all_jobs() -> list[dict]:
    """모든 작업 상태 나열."""
    return job_manager.list_jobs()
