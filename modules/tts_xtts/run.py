from __future__ import annotations
import argparse
from pathlib import Path


def load_config(config_path: Path | None) -> dict:
    if config_path is None:
        return {}
    # TODO: YAML 설정 파일 로드 구현
    return {}


def synthesize_backup(input_json: Path, output_audio: Path, config: dict) -> None:
    # TODO: XTTS 백업 음성 합성 로직 구현
    raise NotImplementedError("XTTS 합성 로직 필요")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--config")
    args = parser.parse_args()

    config_path = Path(args.config) if args.config else None
    config = load_config(config_path)
    synthesize_backup(Path(args.input), Path(args.output), config)


if __name__ == "__main__":
    main()
