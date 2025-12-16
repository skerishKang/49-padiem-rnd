from __future__ import annotations
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

from .routers import audio, files, jobs, lipsync, lipsync_musetalk, rvc, stt, stt_gemini, text, tts, tts_backup, tts_gemini, uploads


load_dotenv()

app = FastAPI(
    title="Padiem RnD 모듈형 더빙 파이프라인 API",
    description="각 파이프라인 모듈을 HTTP API로 노출하고 작업 큐를 지원하는 프로토타입",
    version="0.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8501",
        "http://127.0.0.1:8501",
        "http://localhost:8510",
        "http://127.0.0.1:8510",
        "http://localhost",
        "http://127.0.0.1",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(audio.router)
app.include_router(stt.router)
app.include_router(stt_gemini.router)
app.include_router(text.router)
app.include_router(tts.router)
app.include_router(tts_backup.router)
app.include_router(tts_gemini.router)
app.include_router(rvc.router)
app.include_router(lipsync.router)
app.include_router(lipsync_musetalk.router)
app.include_router(jobs.router)
app.include_router(files.router)
app.include_router(uploads.router)


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
