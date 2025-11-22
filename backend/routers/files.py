from __future__ import annotations

import json

from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import FileResponse, JSONResponse

from ..utils import BASE_DIR, resolve_path


MEDIA_TYPES = {
    ".wav": "audio/wav",
    ".mp3": "audio/mpeg",
    ".flac": "audio/flac",
    ".mp4": "video/mp4",
    ".mov": "video/quicktime",
    ".json": "application/json",
}


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

    media_type = MEDIA_TYPES.get(resolved.suffix.lower())
    return FileResponse(resolved, media_type=media_type)


@router.get("/preview/json")
async def preview_json(path: str = Query(..., min_length=1)) -> JSONResponse:
    resolved = resolve_path(path)
    if not resolved.exists() or resolved.suffix.lower() != ".json":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="JSON 파일을 찾을 수 없습니다.")

    with resolved.open("r", encoding="utf-8") as fp:
        data = json.load(fp)

    return JSONResponse(data)


@router.get("/preview/audio")
async def preview_audio(path: str = Query(..., min_length=1)) -> FileResponse:
    resolved = resolve_path(path)
    if not resolved.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="오디오 파일을 찾을 수 없습니다.")

    media_type = MEDIA_TYPES.get(resolved.suffix.lower(), "audio/wav")
    return FileResponse(resolved, media_type=media_type)


@router.get("/preview/video")
async def preview_video(path: str = Query(..., min_length=1)) -> FileResponse:
    resolved = resolve_path(path)
    if not resolved.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="비디오 파일을 찾을 수 없습니다.")

    media_type = MEDIA_TYPES.get(resolved.suffix.lower(), "video/mp4")
    return FileResponse(resolved, media_type=media_type)


@router.get("/download")
async def download_file(path: str = Query(..., min_length=1)) -> FileResponse:
    resolved = resolve_path(path)
    if not resolved.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="파일을 찾을 수 없습니다.")

    return FileResponse(resolved, filename=resolved.name, media_type="application/octet-stream")
