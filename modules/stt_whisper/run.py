from __future__ import annotations

import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from shared.utils.io_helpers import (
    configure_logging,
    read_wav,
    read_yaml,
    write_json,
)


LOGGER = logging.getLogger("pipeline.stt")


def load_config(config_path: Path) -> dict:
    if not config_path.exists():
        raise FileNotFoundError(f"설정 파일을 찾을 수 없습니다: {config_path}")
    return read_yaml(config_path)


def run_stt(input_audio: Path, output_json: Path, config: dict) -> None:
    if not input_audio.exists():
        raise FileNotFoundError(f"입력 오디오를 찾을 수 없습니다: {input_audio}")

    LOGGER.info("STT 처리를 시작합니다: %s", input_audio)

    params, _ = read_wav(input_audio)
    duration_sec = params["nframes"] / params["framerate"] if params["framerate"] else 0

    dummy_text = config.get(
        "fallback_text",
        "이것은 프로토타입 Whisper STT 결과입니다.",
    )
    transcript = {
        "id": input_audio.stem,
        "created_at": datetime.utcnow().isoformat() + "Z",
        "duration": duration_sec,
        "language": config.get("language", "auto"),
        "segments": [
            {
                "start": 0.0,
                "end": duration_sec,
                "text": dummy_text,
            }
        ],
        "metadata": {
            "sample_rate": params["framerate"],
            "channels": params["nchannels"],
            "frame_count": params["nframes"],
        },
    }

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
