from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

import yaml


SCRIPT_DIR = Path(__file__).resolve().parent
ROOT_DIR = SCRIPT_DIR.parent


def sanitize_run_name(name: str) -> str:
    sanitized = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in name.strip())
    return sanitized or "run"


def resolve_path(path_str: str) -> Path:
    path = Path(path_str)
    if not path.is_absolute():
        path = (SCRIPT_DIR / path).resolve()
    return path


def format_command(command_template: list[str], context: dict[str, str]) -> list[str]:
    return [part.format(**context) for part in command_template]


def run_step(command_template: list[str], context: dict[str, str]) -> None:
    command = format_command(command_template, context)
    subprocess.run(command, check=True, cwd=SCRIPT_DIR)


def load_pipeline_config(config_path: Path) -> dict:
    with config_path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def build_context(args: argparse.Namespace) -> dict[str, str]:
    input_media = resolve_path(args.input_media)
    run_name = args.run_name or sanitize_run_name(input_media.stem)
    run_root = resolve_path(args.run_root)
    run_dir = (run_root / run_name).resolve()
    run_dir.mkdir(parents=True, exist_ok=True)

    context: dict[str, str] = {
        "input_media": str(input_media),
        "run_name": run_name,
        "run_dir": str(run_dir),
        "audio_output": str(run_dir / f"{run_name}_audio.wav"),
        "stt_output": str(run_dir / f"{run_name}_result.json"),
        "text_output": str(run_dir / f"{run_name}_text.json"),
        "tts_output": str(run_dir / f"{run_name}_valle.wav"),
        "xtts_output": str(run_dir / f"{run_name}_xtts.wav"),
        "rvc_output": str(run_dir / f"{run_name}_rvc.wav"),
        "lipsync_output": str(run_dir / f"{run_name}_wav2lip.mp4"),
    }

    if args.speaker_audio:
        context["speaker_audio"] = str(resolve_path(args.speaker_audio))
    else:
        context["speaker_audio"] = ""

    context.update(
        {
            "root_dir": str(ROOT_DIR),
            "modules_dir": str(ROOT_DIR / "modules"),
            "data_dir": str(ROOT_DIR / "data"),
        }
    )

    return context


def apply_placeholders(config: dict, context: dict[str, str]) -> None:
    placeholders = config.get("placeholders", {})
    for key, template in placeholders.items():
        context[key] = template.format(**context)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="모듈 파이프라인 실행")
    parser.add_argument(
        "--config",
        default=str(SCRIPT_DIR / "config.yaml"),
        help="파이프라인 설정 YAML 경로",
    )
    parser.add_argument(
        "--input-media",
        required=True,
        help="오디오를 추출할 입력 미디어 경로",
    )
    parser.add_argument(
        "--run-name",
        help="결과를 저장할 실행 폴더명(미지정 시 입력 파일명 기반)",
    )
    parser.add_argument(
        "--run-root",
        default=str(Path("../data/runs")),
        help="실행 결과를 저장할 루트 디렉터리",
    )
    parser.add_argument(
        "--speaker-audio",
        help="RVC 단계에서 사용할 타깃 화자 음성 경로(선택)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = load_pipeline_config(Path(args.config))
    context = build_context(args)
    apply_placeholders(config, context)

    steps = config.get("steps", {})

    for step_name in ("audio_extract", "stt", "text_process", "tts", "tts_backup", "rvc", "lipsync"):
        command_template = steps.get(step_name)
        if not command_template:
            continue
        run_step(command_template, context)


if __name__ == "__main__":
    main()
