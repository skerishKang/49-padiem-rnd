from __future__ import annotations
import argparse
from pathlib import Path


def load_config(config_path: Path | None) -> dict:
    if config_path is None:
        return {}
    # TODO: YAML 파일 로드 구현
    return {}


def extract_audio(input_media: Path, output_audio: Path, config: dict) -> None:
    # TODO: 멀티미디어에서 오디오 추출 로직 구현
    raise NotImplementedError("오디오 추출 로직 필요")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--config")
    args = parser.parse_args()

    config_path = Path(args.config) if args.config else None
    config = load_config(config_path)
    extract_audio(Path(args.input), Path(args.output), config)


if __name__ == "__main__":
    main()
