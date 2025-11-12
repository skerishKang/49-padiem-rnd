from __future__ import annotations
import argparse
from pathlib import Path


def load_config(config_path: Path | None) -> dict:
    if config_path is None:
        return {}
    # TODO: YAML 설정 파일 로드 구현
    return {}


def apply_lipsync(input_video: Path, input_audio: Path, output_video: Path, config: dict) -> None:
    # TODO: Wav2Lip 기반 립싱크 적용 로직 구현
    raise NotImplementedError("립싱크 적용 로직 필요")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--video", required=True)
    parser.add_argument("--audio", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--config")
    args = parser.parse_args()

    config_path = Path(args.config) if args.config else None
    config = load_config(config_path)
    apply_lipsync(Path(args.video), Path(args.audio), Path(args.output), config)


if __name__ == "__main__":
    main()
