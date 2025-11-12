from __future__ import annotations
import json
from pathlib import Path
from typing import Any


def read_json(json_path: Path) -> Any:
    """JSON 파일 읽기."""
    with json_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(json_path: Path, data: Any) -> None:
    """JSON 파일 저장."""
    json_path.parent.mkdir(parents=True, exist_ok=True)
    with json_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def read_wav(wav_path: Path) -> bytes:
    """WAV 파일을 읽어 바이너리 데이터를 반환."""
    # TODO: WAV 파일 로딩 로직 구현 (예: soundfile, librosa 등 사용)
    raise NotImplementedError("WAV 읽기 로직 필요")


def write_wav(wav_path: Path, audio_data: bytes, sample_rate: int) -> None:
    """WAV 파일로 저장."""
    # TODO: WAV 파일 저장 로직 구현
    raise NotImplementedError("WAV 저장 로직 필요")


def read_mp4(mp4_path: Path) -> bytes:
    """MP4 파일을 읽어 바이너리 데이터를 반환."""
    # TODO: MP4 파일 로딩 로직 구현 (예: moviepy 등 사용)
    raise NotImplementedError("MP4 읽기 로직 필요")


def write_mp4(mp4_path: Path, video_data: bytes) -> None:
    """MP4 파일로 저장."""
    # TODO: MP4 파일 저장 로직 구현
    raise NotImplementedError("MP4 저장 로직 필요")
