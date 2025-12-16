from __future__ import annotations
import sys
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from ..utils import resolve_path, run_module, start_module_job


router = APIRouter(prefix="/tts-gemini", tags=["Gemini TTS"])


class TtsGeminiRequest(BaseModel):
    input_json: str = Field(..., min_length=1)
    output_audio: str = Field(..., min_length=1)
    config: str | None = Field(default=None, min_length=1)
    async_run: bool = False


@router.post("/")
async def run_tts_gemini(request: TtsGeminiRequest) -> dict[str, str]:
    """Gemini TTS 모듈 실행."""
    input_path = resolve_path(request.input_json)
    output_path = resolve_path(request.output_audio)
    if not input_path.exists():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"입력 JSON을 찾을 수 없습니다: {input_path}",
        )

    command = [
        sys.executable,
        "modules/tts_gemini/run.py",
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

    if request.async_run:
        job_id = start_module_job(command, meta={"module": "tts_gemini", "output": str(output_path)})
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
