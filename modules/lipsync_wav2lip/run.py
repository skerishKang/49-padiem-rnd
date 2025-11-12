from __future__ import annotations

import argparse
import logging
import os
import subprocess
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from shared.utils.io_helpers import configure_logging, ensure_parent, read_yaml


LOGGER = logging.getLogger("pipeline.lipsync")


def load_config(config_path: Path | None) -> dict:
    if config_path is None:
        raise ValueError("Wav2Lip 실행을 위해 config 파일이 필요합니다.")
    if not config_path.exists():
        raise FileNotFoundError(f"설정 파일을 찾을 수 없습니다: {config_path}")
    return read_yaml(config_path)


def _build_command(config: dict, input_video: Path, input_audio: Path, output_video: Path) -> tuple[list[str], dict[str, str] | None]:
    script_path = Path(config.get("script_path", ""))
    if not script_path.exists():
        raise FileNotFoundError(f"Wav2Lip 실행 스크립트를 찾을 수 없습니다: {script_path}")

    checkpoint = Path(config.get("checkpoint", ""))
    if not checkpoint.exists():
        raise FileNotFoundError(f"Wav2Lip 체크포인트를 찾을 수 없습니다: {checkpoint}")

    face_detector = Path(config.get("face_detector", ""))
    if not face_detector.exists():
        raise FileNotFoundError(f"Face detector 파라미터를 찾을 수 없습니다: {face_detector}")

    python_exec = config.get("python_executable", sys.executable)
    bbox = config.get("bbox", [])
    nosmooth = config.get("nosmooth", False)

    command = [
        python_exec,
        str(script_path),
        "--checkpoint",
        str(checkpoint),
        "--face",
        str(input_video),
        "--audio",
        str(input_audio),
        "--outfile",
        str(output_video),
        "--face-detector",
        "sfd",
        "--face-detector-config",
        str(face_detector),
    ]

    if bbox:
        command.extend(["--bbox", ",".join(map(str, bbox))])
    if nosmooth:
        command.append("--nosmooth")
    if fps := config.get("fps"):
        command.extend(["--fps", str(fps)])

    env = None
    if env_config := config.get("env"):
        env = {**os.environ, **env_config}

    return command, env


def apply_lipsync(input_video: Path, input_audio: Path, output_video: Path, config: dict) -> None:
    if not input_video.exists():
        raise FileNotFoundError(f"입력 비디오를 찾을 수 없습니다: {input_video}")
    if not input_audio.exists():
        raise FileNotFoundError(f"입력 오디오를 찾을 수 없습니다: {input_audio}")

    ensure_parent(output_video)
    command, env = _build_command(config, input_video, input_audio, output_video)

    LOGGER.info("Wav2Lip 실행: %s", " ".join(command))

    try:
        subprocess.run(command, check=True, env=env)
    except subprocess.CalledProcessError as exc:
        LOGGER.error("Wav2Lip 실행 실패: %s", exc)
        raise RuntimeError("Wav2Lip 실행 중 오류가 발생했습니다.") from exc

    if not output_video.exists():
        raise RuntimeError("Wav2Lip 실행 후 출력 영상이 생성되지 않았습니다.")

    LOGGER.info("립싱크 합성 완료: %s", output_video)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--video", required=True)
    parser.add_argument("--audio", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--config")
    args = parser.parse_args()

    logging_config = ROOT_DIR / "shared" / "logging_config.yaml"
    configure_logging(logging_config)

    config_path = Path(args.config) if args.config else None
    config = load_config(config_path)
    apply_lipsync(Path(args.video), Path(args.audio), Path(args.output), config)


if __name__ == "__main__":
    main()
