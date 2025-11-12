from __future__ import annotations

import argparse
import logging
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
        return {}
    if not config_path.exists():
        raise FileNotFoundError(f"설정 파일을 찾을 수 없습니다: {config_path}")
    return read_yaml(config_path)


def apply_lipsync(input_video: Path, input_audio: Path, output_video: Path, config: dict) -> None:
    if not input_video.exists():
        raise FileNotFoundError(f"입력 비디오를 찾을 수 없습니다: {input_video}")
    if not input_audio.exists():
        raise FileNotFoundError(f"입력 오디오를 찾을 수 없습니다: {input_audio}")

    ffmpeg_path = config.get("ffmpeg_path", "ffmpeg")
    video_codec = config.get("video_codec", "copy")
    audio_codec = config.get("audio_codec", "aac")
    audio_bitrate = config.get("audio_bitrate", "192k")
    extra_args: list[str] = config.get("extra_args", [])

    ensure_parent(output_video)

    command = [
        ffmpeg_path,
        "-y",
        "-i",
        str(input_video),
        "-i",
        str(input_audio),
        "-c:v",
        video_codec,
        "-c:a",
        audio_codec,
        "-b:a",
        audio_bitrate,
        "-map",
        "0:v:0",
        "-map",
        "1:a:0",
    ]
    if extra_args:
        command.extend(extra_args)
    command.append(str(output_video))

    LOGGER.info("FFmpeg 립싱크 합성 실행: %s", " ".join(command))

    try:
        result = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
        )
        if result.stdout:
            LOGGER.debug("ffmpeg stdout: %s", result.stdout)
        if result.stderr:
            LOGGER.debug("ffmpeg stderr: %s", result.stderr)
    except FileNotFoundError as exc:
        LOGGER.error("ffmpeg를 찾을 수 없습니다. 경로를 확인하세요.")
        raise RuntimeError("ffmpeg 실행 파일을 찾을 수 없습니다.") from exc
    except subprocess.CalledProcessError as exc:
        LOGGER.error("립싱크 합성 실패: %s", exc.stderr)
        raise RuntimeError("립싱크 합성 중 오류가 발생했습니다.") from exc

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
