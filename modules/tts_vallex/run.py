from __future__ import annotations

import argparse
import logging
import os
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from shared.utils.io_helpers import (
    configure_logging,
    ensure_parent,
    format_command,
    read_json,
    read_yaml,
)


LOGGER = logging.getLogger("pipeline.tts.vallex")


def load_config(config_path: Path | None) -> dict:
    if config_path is None:
        raise ValueError("VALL-E X 합성을 위해 config 파일이 필요합니다.")
    if not config_path.exists():
        raise FileNotFoundError(f"설정 파일을 찾을 수 없습니다: {config_path}")
    return read_yaml(config_path)


def _prepare_text_payload(input_json: Path, fallback_text: str | None = None) -> str:
    data = read_json(input_json)
    segments = data.get("segments", [])
    texts = [segment.get("processed_text") or segment.get("text", "") for segment in segments]
    combined = " ".join(filter(None, texts)).strip()
    if not combined and fallback_text:
        combined = fallback_text
    if not combined:
        raise ValueError("합성할 텍스트가 비어 있습니다.")
    return combined


def _run_vallex(command: list[str], work_dir: Path | None = None, env: dict[str, str] | None = None) -> None:
    LOGGER.debug("VALL-E X 실행 명령: %s", " ".join(command))
    try:
        subprocess.run(
            command,
            check=True,
            cwd=str(work_dir) if work_dir else None,
            env=env,
        )
    except subprocess.CalledProcessError as exc:
        LOGGER.error("VALL-E X 합성 실패: %s", exc)
        raise RuntimeError("VALL-E X 합성 중 오류가 발생했습니다.") from exc


def synthesize_speech(input_json: Path, output_audio: Path, config: dict) -> None:
    if not input_json.exists():
        raise FileNotFoundError(f"입력 JSON을 찾을 수 없습니다: {input_json}")

    script_path = Path(config.get("script_path", ""))
    if not script_path.exists():
        raise FileNotFoundError(f"VALL-E X 스크립트를 찾을 수 없습니다: {script_path}")

    checkpoint_dir = Path(config.get("checkpoint_dir", ""))
    if not checkpoint_dir.exists():
        raise FileNotFoundError(f"체크포인트 디렉터리를 찾을 수 없습니다: {checkpoint_dir}")

    speaker_id = config.get("speaker_id")
    work_dir = Path(config.get("work_dir", output_audio.parent))
    work_dir.mkdir(parents=True, exist_ok=True)

    text_payload = _prepare_text_payload(input_json, config.get("fallback_text", ""))

    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, dir=work_dir) as tmp_text:
        tmp_text.write(text_payload)
        text_file = Path(tmp_text.name)

    ensure_parent(output_audio)

    python_exec = config.get("python_executable", sys.executable)

    command_template = config.get(
        "command_template",
        [
            "{python}",
            "{script_path}",
            "--checkpoint-dir",
            "{checkpoint_dir}",
            "--input-text",
            "{input_text}",
            "--output-path",
            "{output_audio}",
        ],
    )

    command = format_command(
        command_template,
        python=python_exec,
        script_path=str(script_path),
        checkpoint_dir=str(checkpoint_dir),
        input_text=str(text_file),
        output_audio=str(output_audio),
    )

    if speaker_id:
        command.extend(["--speaker", str(speaker_id)])

    env = None
    if env_config := config.get("env"):
        env = {**os.environ, **env_config}

    try:
        _run_vallex(command, work_dir=work_dir, env=env)
        LOGGER.info("VALL-E X 합성 완료: %s", output_audio)
    finally:
        if text_file.exists():
            try:
                text_file.unlink()
            except OSError:
                LOGGER.warning("임시 텍스트 파일 삭제 실패: %s", text_file)


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
    synthesize_speech(Path(args.input), Path(args.output), config)


if __name__ == "__main__":
    main()
