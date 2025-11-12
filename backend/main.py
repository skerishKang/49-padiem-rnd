from __future__ import annotations
from fastapi import FastAPI

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
