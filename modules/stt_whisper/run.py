from __future__ import annotations

import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import torch
import whisper


ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from shared.utils.io_helpers import configure_logging, ensure_parent, read_yaml, write_json


LOGGER = logging.getLogger("pipeline.stt")


def load_config(config_path: Path) -> dict:
    if not config_path.exists():
        raise FileNotFoundError(f"설정 파일을 찾을 수 없습니다: {config_path}")
    return read_yaml(config_path)


def _load_whisper_model(config: dict) -> whisper.Whisper:
    model_name = config.get("model_name", "large-v3")
    model_dir = config.get("model_dir")
    use_gpu = config.get("use_gpu", True)
    device = "cuda" if use_gpu and torch.cuda.is_available() else "cpu"

    LOGGER.info("Whisper 모델 로드: name=%s, device=%s", model_name, device)
    download_root = Path(model_dir) if model_dir else None
    return whisper.load_model(model_name, device=device, download_root=str(download_root) if download_root else None)


def _build_transcribe_options(config: dict) -> dict[str, Any]:
    language = config.get("language")
    if language in ("auto", "automatic", None):
        language = None

    options: dict[str, Any] = {
        "task": config.get("task", "transcribe"),
        "beam_size": int(config.get("beam_size", 5)),
        "best_of": int(config.get("best_of", 5)),
        "temperature": config.get("temperature", 0.0),
        "verbose": False,
    }
    if language:
        options["language"] = language
    if config.get("initial_prompt"):
        options["initial_prompt"] = config["initial_prompt"]
    if config.get("condition_on_previous_text") is not None:
        options["condition_on_previous_text"] = bool(config["condition_on_previous_text"])
    return options


def _format_segments(raw_segments: list[dict[str, Any]]) -> list[dict[str, Any]]:
    formatted = []
    for idx, segment in enumerate(raw_segments):
        formatted.append(
            {
                "id": int(segment.get("id", idx)),
                "start": float(segment.get("start", 0.0)),
                "end": float(segment.get("end", 0.0)),
                "text": segment.get("text", "").strip(),
            }
        )
    return formatted


def run_stt(input_audio: Path, output_json: Path, config: dict) -> None:
    if not input_audio.exists():
        raise FileNotFoundError(f"입력 오디오를 찾을 수 없습니다: {input_audio}")

    model = _load_whisper_model(config)
    transcribe_options = _build_transcribe_options(config)

    LOGGER.info("Whisper 전사를 시작합니다: %s", input_audio)
    result = model.transcribe(str(input_audio), **transcribe_options)

    segments = _format_segments(result.get("segments", []))
    transcript = {
        "id": input_audio.stem,
        "created_at": datetime.utcnow().isoformat() + "Z",
        "language": result.get("language") or transcribe_options.get("language"),
        "text": result.get("text", "").strip(),
        "speaker_id": config.get("speaker_id"),
        "segments": segments,
        "metadata": {
            "duration": float(result.get("duration", 0.0)),
            "model": config.get("model_name", "large-v3"),
            "task": transcribe_options.get("task"),
            "beam_size": transcribe_options.get("beam_size"),
            "temperature": transcribe_options.get("temperature"),
        },
    }

    ensure_parent(output_json)
    write_json(output_json, transcript)
    LOGGER.info("STT 결과를 저장했습니다: %s", output_json)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--config", default="config/settings.yaml")
    args = parser.parse_args()

    logging_config = ROOT_DIR / "shared" / "logging_config.yaml"
    configure_logging(logging_config)

    config = load_config(Path(args.config))
    run_stt(Path(args.input), Path(args.output), config)


if __name__ == "__main__":
    main()
