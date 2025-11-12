from __future__ import annotations

import argparse
import logging
import sys
from array import array
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from shared.utils.io_helpers import (
    configure_logging,
    ensure_parent,
    read_wav,
    read_yaml,
    write_wav,
)


LOGGER = logging.getLogger("pipeline.rvc")


def load_config(config_path: Path | None) -> dict:
    if config_path is None:
        return {}
    if not config_path.exists():
        raise FileNotFoundError(f"설정 파일을 찾을 수 없습니다: {config_path}")
    return read_yaml(config_path)


def convert_voice(input_audio: Path, output_audio: Path, config: dict) -> None:
    if not input_audio.exists():
        raise FileNotFoundError(f"입력 오디오를 찾을 수 없습니다: {input_audio}")

    LOGGER.info("RVC 음성 변환 시작: %s", input_audio)
    params, frames = read_wav(input_audio)

    pitch_shift = float(config.get("pitch_shift", 0.0))
    volume_scale = float(config.get("volume_scale", 1.1))

    samples = array("h")
    samples.frombytes(frames)

    # 간단한 볼륨 조정과 피치 시프트 모사
    scaled_samples = array("h")
    for idx, sample in enumerate(samples):
        adjusted = int(sample * volume_scale)
        adjusted = max(min(adjusted, 32767), -32768)
        if pitch_shift != 0 and idx + 1 < len(samples):
            neighbor = samples[min(int(idx + pitch_shift), len(samples) - 1)]
            adjusted = int((adjusted + neighbor) / 2)
        scaled_samples.append(adjusted)

    ensure_parent(output_audio)
    write_wav(
        output_audio,
        scaled_samples.tobytes(),
        nchannels=params["nchannels"],
        sampwidth=params["sampwidth"],
        framerate=params["framerate"],
    )
    LOGGER.info("RVC 음성 변환 완료: %s", output_audio)


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
    convert_voice(Path(args.input), Path(args.output), config)


if __name__ == "__main__":
    main()
