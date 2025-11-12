from __future__ import annotations

import argparse
import logging
import math
import sys
from array import array
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from shared.utils.io_helpers import (
    configure_logging,
    ensure_parent,
    read_json,
    read_yaml,
    write_wav,
)


LOGGER = logging.getLogger("pipeline.tts.vallex")


def load_config(config_path: Path | None) -> dict:
    if config_path is None:
        return {}
    if not config_path.exists():
        raise FileNotFoundError(f"설정 파일을 찾을 수 없습니다: {config_path}")
    return read_yaml(config_path)


def build_waveform(text: str, sample_rate: int, base_frequency: float) -> bytes:
    duration_per_char = 0.08
    duration = max(len(text) * duration_per_char, 0.5)
    total_samples = int(duration * sample_rate)
    amplitude = 32767 * 0.3
    waveform = array("h")
    for n in range(total_samples):
        value = int(amplitude * math.sin(2 * math.pi * base_frequency * n / sample_rate))
        waveform.append(value)
    return waveform.tobytes()


def synthesize_speech(input_json: Path, output_audio: Path, config: dict) -> None:
    if not input_json.exists():
        raise FileNotFoundError(f"입력 JSON을 찾을 수 없습니다: {input_json}")

    LOGGER.info("VALL-E X 합성을 시작합니다: %s", input_json)
    data = read_json(input_json)

    sample_rate = int(config.get("sample_rate", 22050))
    base_frequency = float(config.get("base_frequency", 220.0))

    segments = data.get("segments", [])
    texts = [segment.get("processed_text") or segment.get("text", "") for segment in segments]
    full_text = " ".join(filter(None, texts)) or config.get("fallback_text", "테스트 음성입니다.")

    waveform = build_waveform(full_text, sample_rate, base_frequency)

    ensure_parent(output_audio)
    write_wav(output_audio, waveform, nchannels=1, sampwidth=2, framerate=sample_rate)
    LOGGER.info("VALL-E X 합성 완료: %s", output_audio)


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
    synthesize_speech(Path(args.input), Path(args.output), config)


if __name__ == "__main__":
    main()
