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


LOGGER = logging.getLogger("pipeline.audio_extractor")


def load_config(config_path: Path | None) -> dict:
    if config_path is None:
        return {}
    if not config_path.exists():
        raise FileNotFoundError(f"설정 파일을 찾을 수 없습니다: {config_path}")
    return read_yaml(config_path)


def extract_audio(input_media: Path, output_audio: Path, config: dict) -> None:
    if not input_media.exists():
        raise FileNotFoundError(f"입력 미디어를 찾을 수 없습니다: {input_media}")

    ffmpeg_path = config.get("ffmpeg_path", "ffmpeg")
    audio_codec = config.get("audio_codec", "pcm_s16le")
    sample_rate = config.get("sample_rate")
    extra_args: list[str] = config.get("extra_args", [])

    ensure_parent(output_audio)

    command = [
        ffmpeg_path,
        "-y",
        "-i",
        str(input_media),
        "-vn",
        "-acodec",
        audio_codec,
    ]
    if sample_rate:
        command.extend(["-ar", str(sample_rate)])
    if extra_args:
        command.extend(extra_args)
    command.append(str(output_audio))

    LOGGER.info("FFmpeg 오디오 추출 실행: %s", " ".join(command))

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
        LOGGER.error("오디오 추출 실패: %s", exc.stderr)
        raise RuntimeError("오디오 추출 중 오류가 발생했습니다.") from exc

    LOGGER.info("오디오 추출 완료: %s", output_audio)


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
    extract_audio(Path(args.input), Path(args.output), config)


if __name__ == "__main__":
    main()
