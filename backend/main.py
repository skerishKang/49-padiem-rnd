from __future__ import annotations
from fastapi import FastAPI
from fastapi.responses import JSONResponse

from .routers import audio, jobs, lipsync, rvc, stt, text, tts, tts_backup


app = FastAPI(
    title="Padiem RnD 모듈형 더빙 파이프라인 API",
    description="각 파이프라인 모듈을 HTTP API로 노출하고 작업 큐를 지원하는 프로토타입",
    version="0.2.0",
)

app.include_router(audio.router)
app.include_router(stt.router)
app.include_router(text.router)
app.include_router(tts.router)
app.include_router(tts_backup.router)
app.include_router(rvc.router)
app.include_router(lipsync.router)
app.include_router(jobs.router)


@app.get("/health", tags=["Health"])
async def health_check() -> dict[str, str]:
    """상태 점검 엔드포인트."""
    return {"status": "ok"}


@app.get("/api/{service}/{remaining:path}", include_in_schema=False)
async def external_service_placeholder(service: str, remaining: str = "") -> JSONResponse:
    """미구현 외부 서비스 요청에 대한 안내."""
    full_path = "/".join(part for part in ("api", service, remaining) if part)
    return JSONResponse(
        status_code=404,
        content={
            "detail": "외부 서비스 연동이 아직 구성되지 않았습니다.",
            "path": f"/{full_path}",
        },
    )
