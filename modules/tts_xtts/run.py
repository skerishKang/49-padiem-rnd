from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path
from typing import Optional

from TTS.api import TTS


ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from shared.utils.io_helpers import (
    configure_logging,
    ensure_parent,
    read_json,
    read_yaml,
)


LOGGER = logging.getLogger("pipeline.tts.xtts")


def load_config(config_path: Path | None) -> dict:
    if config_path is None:
        raise ValueError("XTTS 합성을 위해 config 파일이 필요합니다.")
    if not config_path.exists():
        raise FileNotFoundError(f"설정 파일을 찾을 수 없습니다: {config_path}")
    return read_yaml(config_path)


def _prepare_text(input_json: Path, fallback_text: str | None = None) -> str:
    data = read_json(input_json)
    segments = data.get("segments", [])
    texts = [segment.get("processed_text") or segment.get("text", "") for segment in segments]
    combined = " ".join(filter(None, texts)).strip()
    if not combined and fallback_text:
        combined = fallback_text
    if not combined:
        raise ValueError("합성할 텍스트가 비어 있습니다.")
    return combined


def _load_tts_model(config: dict) -> TTS:
    model_name = config.get("model_name", "tts_models/multilingual/multi-dataset/xtts_v2")
    use_gpu = config.get("use_gpu", True)
    LOGGER.info("XTTS 모델 로드: %s (GPU=%s)", model_name, use_gpu)
    return TTS(model_name=model_name, progress_bar=False, gpu=use_gpu)


def _resolve_speaker_wav(config: dict) -> Optional[str]:
    speaker_wav = config.get("speaker_wav")
    if speaker_wav:
        path = Path(speaker_wav)
        if not path.exists():
            raise FileNotFoundError(f"스피커 참조 음성을 찾을 수 없습니다: {path}")
        return str(path)
    return None


def synthesize_backup(input_json: Path, output_audio: Path, config: dict) -> None:
    if not input_json.exists():
        raise FileNotFoundError(f"입력 JSON을 찾을 수 없습니다: {input_json}")

    LOGGER.info("XTTS 백업 합성을 시작합니다: %s", input_json)
    text = _prepare_text(input_json, config.get("fallback_text"))
    speaker_wav = _resolve_speaker_wav(config)

    tts = _load_tts_model(config)

    ensure_parent(output_audio)
    synthesis_kwargs = {
        "text": text,
        "file_path": str(output_audio),
    }
    if speaker_wav:
        synthesis_kwargs["speaker_wav"] = speaker_wav
    if language := config.get("language"):
        synthesis_kwargs["language"] = language

    try:
        tts.tts_to_file(**synthesis_kwargs)
    except Exception as exc:  # noqa: BLE001
        LOGGER.exception("XTTS 합성 실패")
        raise RuntimeError("XTTS 합성 중 오류가 발생했습니다.") from exc

    LOGGER.info("XTTS 백업 합성 완료: %s", output_audio)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--config")
    args = parser.parse_args()

    logging_config = ROOT_DIR / "shared" / "logging_config.yaml"
    configure_logging(logging_config)

    config_path = Path(args.config) if args.config else None
    config = load_config(config_path)
    synthesize_backup(Path(args.input), Path(args.output), config)


if __name__ == "__main__":
    main()
