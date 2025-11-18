from __future__ import annotations
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from ..utils import resolve_path, run_module, start_module_job


router = APIRouter(prefix="/text", tags=["Text Processor"])


class TextProcessRequest(BaseModel):
    input_json: str = Field(..., min_length=1)
    output_json: str = Field(..., min_length=1)
    config: str | None = Field(default=None, min_length=1)
    async_run: bool = False
    source_language: str | None = Field(default="en", description="원본 언어 (비어있으면 입력 JSON의 language 필드 또는 'en' 사용)")
    target_language: str | None = Field(default="ko", description="번역 언어 (기본값 'ko')")


@router.post("/process")
async def process_text(request: TextProcessRequest) -> dict[str, str]:
    """텍스트 전처리/번역 모듈 실행."""
    input_path = resolve_path(request.input_json)
    output_path = resolve_path(request.output_json)
    if not input_path.exists():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"입력 JSON을 찾을 수 없습니다: {input_path}",
        )

    command = [
        "python",
        "modules/text_processor/run.py",
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

    if request.source_language:
        command.extend(["--source-language", request.source_language])
    if request.target_language:
        command.extend(["--target-language", request.target_language])

    if request.async_run:
        job_id = start_module_job(command, meta={"module": "text_processor", "output": str(output_path)})
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