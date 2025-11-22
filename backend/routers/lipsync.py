from __future__ import annotations
import sys
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from ..utils import resolve_path, run_module, start_module_job


router = APIRouter(prefix="/lipsync", tags=["Wav2Lip"])


class LipSyncRequest(BaseModel):
    input_video: str = Field(..., min_length=1)
    input_audio: str = Field(..., min_length=1)
    output_video: str = Field(..., min_length=1)
    config: str | None = Field(default=None, min_length=1)
    async_run: bool = False


@router.post("/")
async def apply_lipsync(request: LipSyncRequest) -> dict[str, str]:
    """Wav2Lip 립싱크 모듈 실행."""
    video_path = resolve_path(request.input_video)
    audio_path = resolve_path(request.input_audio)
    output_path = resolve_path(request.output_video)

    if not video_path.exists():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"입력 비디오를 찾을 수 없습니다: {video_path}",
        )
    if not audio_path.exists():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"입력 오디오를 찾을 수 없습니다: {audio_path}",
        )

    command = [
        sys.executable,
        "modules/lipsync_wav2lip/run.py",
        "--video",
        str(video_path),
        "--audio",
        str(audio_path),
        "--output",
        str(output_path),
    ]
    if request.config:
        config_path = resolve_path(request.config)
        if not config_path.exists():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"설정 파일을 찾을 수 없습니다: {config_path}",
            )
        command.extend(["--config", str(config_path)])

    if request.async_run:
        job_id = start_module_job(command, meta={"module": "lipsync", "output": str(output_path)})
        return {"status": "queued", "job_id": job_id}

    try:
        result = run_module(command)
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return {
        "status": "success",
        "output": str(output_path),
        "stdout": result.get("stdout", ""),
        "stderr": result.get("stderr", ""),
    }
