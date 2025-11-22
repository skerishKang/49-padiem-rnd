from __future__ import annotations
import sys
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from ..utils import resolve_path, run_module, start_module_job


router = APIRouter(prefix="/tts-backup", tags=["XTTS"])


class TtsBackupRequest(BaseModel):
    input_json: str = Field(..., min_length=1)
    output_audio: str = Field(..., min_length=1)
    config: str | None = Field(default=None, min_length=1)
    speaker_wav: str | None = Field(default=None, min_length=1)
    language: str | None = Field(default=None, min_length=1)
    async_run: bool = False


@router.post("/")
async def synthesize_backup(request: TtsBackupRequest) -> dict[str, str]:
    """XTTS 백업 음성 합성 모듈 실행."""
    input_path = resolve_path(request.input_json)
    output_path = resolve_path(request.output_audio)
    if not input_path.exists():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"입력 JSON을 찾을 수 없습니다: {input_path}",
        )

    command = [
        sys.executable,
        "modules/tts_xtts/run.py",
        "--input",
        str(input_path),
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
    
    if request.speaker_wav:
        speaker_path = resolve_path(request.speaker_wav)
        if not speaker_path.exists():
             raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"스피커 참조 음성을 찾을 수 없습니다: {speaker_path}",
            )
        command.extend(["--speaker-wav", str(speaker_path)])

    if request.language:
        command.extend(["--language", request.language])

    if request.async_run:
        job_id = start_module_job(command, meta={"module": "tts_backup", "output": str(output_path)})
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
