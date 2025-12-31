from __future__ import annotations

import argparse
import json
import logging
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import soundfile as sf

try:
    import librosa
except ImportError:
    librosa = None


ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from shared.utils.io_helpers import (
    configure_logging,
    ensure_parent,
    read_yaml,
)


LOGGER = logging.getLogger("pipeline.rvc")


def load_config(config_path: Path | None) -> dict:
    if config_path is None:
        raise ValueError("RVC 변환을 위해 config 파일이 필요합니다.")
    if not config_path.exists():
        raise FileNotFoundError(f"설정 파일을 찾을 수 없습니다: {config_path}")
    return read_yaml(config_path)


def _build_command(config: dict, input_audio: Path, output_audio: Path) -> tuple[list[str], dict[str, str] | None]:
    script_path = Path(config.get("script_path", ""))
    if not script_path.exists():
        raise FileNotFoundError(f"RVC 실행 스크립트를 찾을 수 없습니다: {script_path}")

    checkpoint = Path(config.get("checkpoint", ""))
    if not checkpoint.exists():
        raise FileNotFoundError(f"RVC 체크포인트를 찾을 수 없습니다: {checkpoint}")

    python_exec = config.get("python_executable", sys.executable)
    f0_method = config.get("f0_method", "harvest")
    index_path = config.get("index", "")
    index_path = Path(index_path) if index_path else None
    speaker_id = config.get("speaker_id", 0)
    hop_length = config.get("hop_length", 128)
    filter_radius = config.get("filter_radius", 3)

    command = [
        python_exec,
        str(script_path),
        "--model",
        str(checkpoint),
        "--source",
        str(input_audio),
        "--output",
        str(output_audio),
        "--f0",
        f0_method,
        "--hop-length",
        str(hop_length),
        "--filter-radius",
        str(filter_radius),
        "--spk-id",
        str(speaker_id),
    ]

    if index_path and index_path.exists():
        command.extend(["--index", str(index_path)])
    if pitch_shift := config.get("pitch_shift"):
        command.extend(["--pitch", str(pitch_shift)])

    env = None
    if env_config := config.get("env"):
        env = {**os.environ, **env_config}

    return command, env


def _apply_augmentations(source: Path, config: dict) -> Path:
    """
    ffmpeg 기반 증강: 시간 늘이기/줄이기(atempo), 저역/고역 EQ, 노이즈 믹스.
    """
    augment_cfg = config.get("augment", {}) or {}
    filters: list[str] = []

    time_stretch = augment_cfg.get("time_stretch")  # 예: 0.9~1.1
    formant_preserve = bool(augment_cfg.get("formant_preserve", False))

    stretched_path: Path | None = None
    if time_stretch and formant_preserve and librosa:
        # librosa phase vocoder 기반 타임스트레치(피치 유지)
        y, sr = librosa.load(source, sr=None, mono=True)
        atempo = max(0.5, min(2.0, float(time_stretch)))
        y_stretch = librosa.effects.time_stretch(y, atempo)
        stretched_path = Path(tempfile.mkstemp(suffix=".wav")[1])
        sf.write(stretched_path, y_stretch, sr)
        LOGGER.info("formant_preserve 적용: librosa phase vocoder atempo=%s", atempo)
    elif time_stretch:
        atempo = max(0.5, min(2.0, float(time_stretch)))
        filters.append(f"atempo={atempo}")
    elif formant_preserve and not librosa:
        LOGGER.warning("formant_preserve 요청되었으나 librosa 미설치로 ffmpeg atempo로 대체합니다.")

    base_source = stretched_path if stretched_path else source

    low_shelf = augment_cfg.get("bass_gain_db")
    if low_shelf:
        filters.append(f"bass=g={float(low_shelf)}")

    high_shelf = augment_cfg.get("treble_gain_db")
    if high_shelf:
        filters.append(f"treble=g={float(high_shelf)}")

    noise_db = augment_cfg.get("noise_db")

    ffmpeg_path = augment_cfg.get("ffmpeg_path") or "ffmpeg"
    ffmpeg_exists = Path(ffmpeg_path).exists()
    if not ffmpeg_exists:
        LOGGER.warning("ffmpeg 경로를 확인하세요. 설정값=%s (PATH에 있다면 무시 가능)", ffmpeg_path)

    # 노이즈가 없고 필터도 없으면 원본 반환
    if not filters and noise_db is None:
        return source

    tmp = Path(tempfile.mkstemp(suffix=".wav")[1])

    if noise_db is not None:
        # 입력 오디오 길이 파악
        duration = 0.0
        try:
            if librosa:
                duration = librosa.get_duration(path=base_source)
            else:
                info = sf.info(base_source)
                duration = info.duration
        except Exception as e:
            LOGGER.warning("오디오 길이를 측정할 수 없어 기본값 10초를 사용합니다: %s", e)
            duration = 10.0

        # 노이즈 믹스: anoisesrc + amix
        amplitude = max(0.0, min(1.0, 10 ** (float(noise_db) / 20)))
        filter_complex_parts = []
        if filters:
            filter_complex_parts.append(f"[0:a]{','.join(filters)}[a0]")
            pre = "[a0]"
        else:
            pre = "[0:a]"
        filter_complex_parts.append(
            f"anoisesrc=color=white:amplitude={amplitude}:duration={duration}[n];{pre}[n]amix=inputs=2:weights=1 0.3:normalize=0[aout]"
        )
        filter_complex = ";".join(filter_complex_parts)
        command = [
            ffmpeg_path,
            "-y",
            "-i",
            str(base_source),
            "-filter_complex",
            filter_complex,
            "-map",
            "[aout]",
            str(tmp),
        ]
    else:
        command = [
            ffmpeg_path,
            "-y",
            "-i",
            str(base_source),
            "-af",
            ",".join(filters),
            str(tmp),
        ]

    LOGGER.info("RVC 증강 적용: %s", " ".join(command))
    subprocess.run(command, check=True)

    return tmp


def convert_voice(input_audio: Path, output_audio: Path, config: dict) -> None:
    if not input_audio.exists():
        raise FileNotFoundError(f"입력 오디오를 찾을 수 없습니다: {input_audio}")

    ensure_parent(output_audio)
    # 증강 적용(옵션)
    augmented_audio = _apply_augmentations(input_audio, config)

    command, env = _build_command(config, augmented_audio, output_audio)

    LOGGER.info("RVC 변환 실행: %s", " ".join(command))

    try:
        subprocess.run(command, check=True, env=env)
    except subprocess.CalledProcessError as exc:
        LOGGER.error("RVC 변환 실패: %s", exc)
        raise RuntimeError("RVC 변환 중 오류가 발생했습니다.") from exc

    if not output_audio.exists():
        raise RuntimeError("RVC 변환 후 출력 파일이 생성되지 않았습니다.")

    LOGGER.info("RVC 음성 변환 완료: %s", output_audio)


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
    convert_voice(Path(args.input), Path(args.output), config)


if __name__ == "__main__":
    main()
