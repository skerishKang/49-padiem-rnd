from __future__ import annotations

import json
import logging
import logging.config
import wave
from pathlib import Path
from typing import Any, Iterable

import yaml


def ensure_parent(path: Path) -> None:
    """파일 기록 전 부모 디렉터리를 생성."""
    path.parent.mkdir(parents=True, exist_ok=True)


def read_json(json_path: Path) -> Any:
    """JSON 파일 읽기."""
    with json_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(json_path: Path, data: Any) -> None:
    """JSON 파일 저장."""
    ensure_parent(json_path)
    with json_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def read_yaml(yaml_path: Path) -> dict:
    """YAML 설정 로드."""
    with yaml_path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def read_wav(wav_path: Path) -> tuple[dict[str, int], bytes]:
    """WAV 파일을 읽어 파라미터와 오디오 프레임 반환."""
    with wave.open(str(wav_path), "rb") as wav_file:
        params = {
            "nchannels": wav_file.getnchannels(),
            "sampwidth": wav_file.getsampwidth(),
            "framerate": wav_file.getframerate(),
            "nframes": wav_file.getnframes(),
            "comptype": wav_file.getcomptype(),
            "compname": wav_file.getcompname(),
        }
        frames = wav_file.readframes(params["nframes"])
    return params, frames


def write_wav(
    wav_path: Path,
    frames: bytes,
    nchannels: int,
    sampwidth: int,
    framerate: int,
) -> None:
    """WAV 파일 저장."""
    ensure_parent(wav_path)
    with wave.open(str(wav_path), "wb") as wav_file:
        wav_file.setnchannels(nchannels)
        wav_file.setsampwidth(sampwidth)
        wav_file.setframerate(framerate)
        wav_file.writeframes(frames)


def read_mp4(mp4_path: Path) -> bytes:
    """MP4 파일을 바이너리로 반환."""
    return mp4_path.read_bytes()


def write_mp4(mp4_path: Path, video_data: bytes) -> None:
    """MP4 파일 저장."""
    ensure_parent(mp4_path)
    mp4_path.write_bytes(video_data)


def configure_logging(config_path: Path | None = None) -> None:
    """공통 로깅 설정을 적용."""
    default_config = {
        "version": 1,
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": "INFO",
            }
        },
        "root": {"level": "INFO", "handlers": ["console"]},
    }
    if config_path and config_path.exists():
        try:
            with config_path.open("r", encoding="utf-8") as f:
                logging.config.dictConfig(yaml.safe_load(f))
            return
        except Exception:  # pragma: no cover - 로깅 기본값으로 폴백
            logging.basicConfig(level=logging.INFO)
            return
    logging.config.dictConfig(default_config)


def format_command(template: Iterable[str], **kwargs: str) -> list[str]:
    """명령 템플릿에서 플레이스홀더를 채운 리스트 생성."""
    return [part.format(**kwargs) for part in template]
