from __future__ import annotations

import json
import wave
from pathlib import Path
from types import SimpleNamespace

import pytest

from modules import audio_extractor
from modules.stt_whisper import run as stt_run
from modules.tts_vallex import run as vallex_run
from modules.tts_xtts import run as xtts_run
from modules.voice_conversion_rvc import run as rvc_run
from modules.lipsync_wav2lip import run as lipsync_run


@pytest.fixture()
def temp_wav(tmp_path: Path) -> Path:
    path = tmp_path / "input.wav"
    with wave.open(str(path), "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(16000)
        wav_file.writeframes(b"\x00\x00" * 1600)
    return path


def test_stt_whisper_runs_with_mock(monkeypatch: pytest.MonkeyPatch, temp_wav: Path, tmp_path: Path) -> None:
    config_path = tmp_path / "stt.yaml"
    config_path.write_text(
        """
model_name: large-v3
model_dir: "{model_dir}"
use_gpu: false
language: auto
beam_size: 2
best_of: 2
""".strip().format(model_dir=tmp_path.as_posix()),
        encoding="utf-8",
    )

    fake_result = {
        "text": "안녕하세요",
        "language": "ko",
        "duration": 1.0,
        "segments": [
            {"id": 0, "start": 0.0, "end": 1.0, "text": "안녕하세요"},
        ],
    }

    class FakeModel:
        def transcribe(self, *_args, **_kwargs):
            return fake_result

    monkeypatch.setattr(stt_run.whisper, "load_model", lambda *a, **k: FakeModel())

    config = stt_run.load_config(config_path)
    output_json = tmp_path / "stt.json"
    stt_run.run_stt(temp_wav, output_json, config)

    data = json.loads(output_json.read_text(encoding="utf-8"))
    assert data["text"] == fake_result["text"]
    assert data["segments"][0]["text"] == "안녕하세요"


def test_vallex_command_construction(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    script_path = tmp_path / "run_vallex.py"
    script_path.write_text("print('vallex')", encoding="utf-8")
    checkpoint_dir = tmp_path / "ckpt"
    checkpoint_dir.mkdir()

    input_json = tmp_path / "input.json"
    input_json.write_text(
        json.dumps(
            {
                "segments": [
                    {"text": "테스트 문장"},
                ]
            }
        ),
        encoding="utf-8",
    )
    output_audio = tmp_path / "output.wav"

    captured: dict[str, list[str]] = {}

    def fake_run(command: list[str], **_kwargs) -> None:
        captured["command"] = command
        output_audio.write_bytes(b"fake")

    monkeypatch.setattr(vallex_run, "_run_vallex", fake_run)

    config_path = tmp_path / "vallex.yaml"
    config_path.write_text(
        json.dumps(
            {
                "script_path": script_path.as_posix(),
                "checkpoint_dir": checkpoint_dir.as_posix(),
                "python_executable": sys.executable,
                "fallback_text": "테스트",
            }
        )
    )
    config = {
        "script_path": script_path,
        "checkpoint_dir": checkpoint_dir,
        "python_executable": sys.executable,
        "fallback_text": "테스트",
    }

    vallex_run.synthesize_speech(input_json, output_audio, config)
    assert output_audio.exists()
    assert "command" in captured
    assert script_path.as_posix() in captured["command"]


def test_xtts_generates_audio(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    input_json = tmp_path / "text.json"
    input_json.write_text(
        json.dumps(
            {
                "segments": [
                    {"processed_text": "샘플 텍스트"},
                ]
            }
        ),
        encoding="utf-8",
    )
    output_audio = tmp_path / "xtts.wav"

    class FakeTTS:
        def __init__(self, *args, **kwargs):
            pass

        def tts_to_file(self, text: str, file_path: str, **kwargs) -> None:
            Path(file_path).write_bytes(text.encode("utf-8"))

    monkeypatch.setattr(xtts_run, "TTS", FakeTTS)

    config = {
        "model_name": "tts_models/multilingual/multi-dataset/xtts_v2",
        "use_gpu": False,
        "fallback_text": "대체 텍스트",
    }

    xtts_run.synthesize_backup(input_json, output_audio, config)
    assert output_audio.exists()


def test_rvc_command(monkeypatch: pytest.MonkeyPatch, temp_wav: Path, tmp_path: Path) -> None:
    script_path = tmp_path / "run_rvc.py"
    script_path.write_text("print('rvc')", encoding="utf-8")
    checkpoint = tmp_path / "rvc.pth"
    checkpoint.write_bytes(b"model")
    output_audio = tmp_path / "rvc.wav"

    def fake_run(command: list[str], check: bool, env: dict | None = None) -> None:
        assert "--model" in command
        Path(command[command.index("--output") + 1]).write_bytes(b"fake")

    monkeypatch.setattr(subprocess, "run", fake_run)

    config = {
        "script_path": script_path.as_posix(),
        "checkpoint": checkpoint.as_posix(),
        "python_executable": sys.executable,
    }

    rvc_run.convert_voice(temp_wav, output_audio, config)
    assert output_audio.exists()


def test_wav2lip_command(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    script_path = tmp_path / "run_wav2lip.py"
    script_path.write_text("print('wav2lip')", encoding="utf-8")
    checkpoint = tmp_path / "wav2lip.pth"
    checkpoint.write_bytes(b"model")
    face_detector = tmp_path / "s3fd.pth"
    face_detector.write_bytes(b"face")

    input_video = tmp_path / "video.mp4"
    input_video.write_bytes(b"video")
    input_audio = tmp_path / "audio.wav"
    input_audio.write_bytes(b"audio")
    output_video = tmp_path / "out.mp4"

    def fake_run(command: list[str], check: bool, env: dict | None = None) -> None:
        assert "--face" in command
        Path(command[command.index("--outfile") + 1]).write_bytes(b"fake")

    monkeypatch.setattr(subprocess, "run", fake_run)

    config = {
        "script_path": script_path.as_posix(),
        "checkpoint": checkpoint.as_posix(),
        "face_detector": face_detector.as_posix(),
        "python_executable": sys.executable,
    }

    lipsync_run.apply_lipsync(input_video, input_audio, output_video, config)
    assert output_video.exists()
