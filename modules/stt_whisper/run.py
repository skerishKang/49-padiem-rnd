from __future__ import annotations
import argparse
from pathlib import Path


def load_config(config_path: Path) -> dict:
    # TODO: YAML 설정 파일 로드 구현
    return {}


def run_stt(input_audio: Path, output_json: Path, config: dict) -> None:
    # TODO: Whisper STT 호출 및 결과 저장 로직 구현
    raise NotImplementedError("STT 처리 로직 필요")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--config", default="config/settings.yaml")
    args = parser.parse_args()

    config = load_config(Path(args.config))
    run_stt(Path(args.input), Path(args.output), config)


if __name__ == "__main__":
    main()
