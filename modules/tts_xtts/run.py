from __future__ import annotations

import argparse
import logging
import math
import random
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


LOGGER = logging.getLogger("pipeline.tts.xtts")


def load_config(config_path: Path | None) -> dict:
    if config_path is None:
        return {}
    if not config_path.exists():
        raise FileNotFoundError(f"설정 파일을 찾을 수 없습니다: {config_path}")
    return read_yaml(config_path)


def build_noise_waveform(length: int, amplitude: float) -> array:
    rng = random.Random(42)
    samples = array("h")
    for _ in range(length):
        samples.append(int(rng.uniform(-amplitude, amplitude)))
    return samples


def synthesize_backup(input_json: Path, output_audio: Path, config: dict) -> None:
    if not input_json.exists():
        raise FileNotFoundError(f"입력 JSON을 찾을 수 없습니다: {input_json}")

    LOGGER.info("XTTS 백업 합성을 시작합니다: %s", input_json)
    data = read_json(input_json)

    sample_rate = int(config.get("sample_rate", 16000))
    duration_sec = float(config.get("min_duration", 3.0))

    segment_count = len(data.get("segments", [])) or 1
    total_samples = int(sample_rate * max(duration_sec, segment_count))
    amplitude = 32767 * 0.1

    base_wave = build_noise_waveform(total_samples, amplitude)

    ensure_parent(output_audio)
    write_wav(output_audio, base_wave.tobytes(), nchannels=1, sampwidth=2, framerate=sample_rate)
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
