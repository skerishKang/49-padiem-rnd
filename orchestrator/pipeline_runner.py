from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

import yaml


SCRIPT_DIR = Path(__file__).resolve().parent


def run_step(command: list[str]) -> None:
    subprocess.run(command, check=True, cwd=SCRIPT_DIR)


def load_pipeline_config(config_path: Path) -> dict:
    with config_path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="모듈 파이프라인 실행")
    parser.add_argument(
        "--config",
        default=str(SCRIPT_DIR / "config.yaml"),
        help="파이프라인 설정 YAML 경로",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = load_pipeline_config(Path(args.config))
    steps = config.get("steps", {})

    if "audio_extract" in steps:
        run_step(steps["audio_extract"])
    if "stt" in steps:
        run_step(steps["stt"])
    if "text_process" in steps:
        run_step(steps["text_process"])
    if "tts" in steps:
        run_step(steps["tts"])
    if "tts_backup" in steps:
        run_step(steps["tts_backup"])
    if "rvc" in steps:
        run_step(steps["rvc"])
    if "lipsync" in steps:
        run_step(steps["lipsync"])


if __name__ == "__main__":
    main()
