"""세션 상태를 파일에 저장하고 복원하는 유틸리티"""
import json
from pathlib import Path
from typing import Any


SESSION_FILE = Path(".streamlit/last_session.json")


def save_session_data(data: dict[str, Any]) -> None:
    """세션 데이터를 파일에 저장 (기존 데이터와 병합)"""
    SESSION_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    existing_data = {}
    if SESSION_FILE.exists():
        try:
            existing_data = json.loads(SESSION_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    
    existing_data.update(data)
    SESSION_FILE.write_text(json.dumps(existing_data, ensure_ascii=False, indent=2), encoding="utf-8")


def load_session_data() -> dict[str, Any]:
    """저장된 세션 데이터를 불러옴"""
    if not SESSION_FILE.exists():
        return {}
    try:
        return json.loads(SESSION_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}
