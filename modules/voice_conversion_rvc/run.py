from __future__ import annotations

import argparse
import json
import logging
import os
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from shared.utils.io_helpers import (
    configure_logging,
    ensure_parent,
    read_yaml,
)


LOGGER = logging.getLogger("pipeline.rvc")


def load_config(config_path: Path | None) -> dict:
    if config_path is None:
        raise ValueError("RVC 변환을 위해 config 파일이 필요합니다.")
    if not config_path.exists():
        raise FileNotFoundError(f"설정 파일을 찾을 수 없습니다: {config_path}")
    return read_yaml(config_path)


def _build_command(config: dict, input_audio: Path, output_audio: Path) -> tuple[list[str], dict[str, str] | None]:
    script_path = Path(config.get("script_path", ""))
    if not script_path.exists():
        raise FileNotFoundError(f"RVC 실행 스크립트를 찾을 수 없습니다: {script_path}")

    checkpoint = Path(config.get("checkpoint", ""))
    if not checkpoint.exists():
        raise FileNotFoundError(f"RVC 체크포인트를 찾을 수 없습니다: {checkpoint}")

    python_exec = config.get("python_executable", sys.executable)
    f0_method = config.get("f0_method", "harvest")
    index_path = config.get("index", "")
    index_path = Path(index_path) if index_path else None
    speaker_id = config.get("speaker_id", 0)
    hop_length = config.get("hop_length", 128)
    filter_radius = config.get("filter_radius", 3)

    command = [
        python_exec,
        str(script_path),
        "--model",
        str(checkpoint),
        "--source",
        str(input_audio),
        "--output",
        str(output_audio),
        "--f0",
        f0_method,
        "--hop-length",
        str(hop_length),
        "--filter-radius",
        str(filter_radius),
        "--spk-id",
        str(speaker_id),
    ]

    if index_path and index_path.exists():
        command.extend(["--index", str(index_path)])
    if pitch_shift := config.get("pitch_shift"):
        command.extend(["--pitch", str(pitch_shift)])

    env = None
    if env_config := config.get("env"):
        env = {**os.environ, **env_config}

    return command, env


def convert_voice(input_audio: Path, output_audio: Path, config: dict) -> None:
    if not input_audio.exists():
        raise FileNotFoundError(f"입력 오디오를 찾을 수 없습니다: {input_audio}")

    ensure_parent(output_audio)
    command, env = _build_command(config, input_audio, output_audio)

    LOGGER.info("RVC 변환 실행: %s", " ".join(command))

    try:
        subprocess.run(command, check=True, env=env)
    except subprocess.CalledProcessError as exc:
        LOGGER.error("RVC 변환 실패: %s", exc)
        raise RuntimeError("RVC 변환 중 오류가 발생했습니다.") from exc

    if not output_audio.exists():
        raise RuntimeError("RVC 변환 후 출력 파일이 생성되지 않았습니다.")

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
