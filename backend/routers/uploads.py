from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status

from ..utils import BASE_DIR, resolve_path


router = APIRouter(prefix="/uploads", tags=["File Uploads"])


@router.post("")
async def upload_file(
    file: UploadFile = File(...),
    target_path: str | None = Form(default=None),
) -> dict[str, str]:
    """클라이언트에서 업로드한 파일을 프로젝트 디렉터리에 저장."""

    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="파일 이름이 비어 있습니다.")

    normalized_target = (target_path or "").strip()
    if normalized_target:
        destination = resolve_path(normalized_target)
    else:
        destination = _default_destination(file.filename)

    _ensure_within_base(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)

    with destination.open("wb") as buffer:
        while True:
            chunk = await file.read(1024 * 1024)
            if not chunk:
                break
            buffer.write(chunk)
    await file.close()

    relative_path = destination.relative_to(BASE_DIR)
    return {"status": "success", "path": str(relative_path).replace("\\", "/")}


def _default_destination(filename: str) -> Path:
    safe_name = Path(filename).name or "upload.bin"
    base_dir = BASE_DIR / "data" / "uploads"
    base_dir.mkdir(parents=True, exist_ok=True)
    candidate = base_dir / safe_name
    counter = 1
    while candidate.exists():
        candidate = base_dir / f"{counter}_{safe_name}"
        counter += 1
    return candidate


def _ensure_within_base(path: Path) -> None:
    try:
        path.relative_to(BASE_DIR)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="허용되지 않은 경로 요청입니다.",
        ) from exc
