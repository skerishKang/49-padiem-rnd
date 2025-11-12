from __future__ import annotations
import subprocess
from pathlib import Path
import yaml


def run_step(command: list[str]) -> None:
    subprocess.run(command, check=True)


def load_pipeline_config(config_path: Path) -> dict:
    with config_path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def main() -> None:
    config = load_pipeline_config(Path("config.yaml"))
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
