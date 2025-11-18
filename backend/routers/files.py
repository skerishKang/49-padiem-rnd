from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import FileResponse

from ..utils import BASE_DIR, resolve_path


router = APIRouter(prefix="/files", tags=["File Serving"])


@router.get("")
async def serve_file(path: str = Query(..., min_length=1)) -> FileResponse:
    """프로젝트 내 파일을 안전하게 서빙."""

    resolved = resolve_path(path)
    try:
        resolved.relative_to(BASE_DIR)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="허용되지 않은 경로입니다.",
        ) from exc

    if not resolved.exists() or not resolved.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="요청한 파일을 찾을 수 없습니다.",
        )

    return FileResponse(resolved)
