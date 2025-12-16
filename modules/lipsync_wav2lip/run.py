from __future__ import annotations

import argparse
import logging
import os
import subprocess
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from shared.utils.io_helpers import configure_logging, ensure_parent, read_yaml


LOGGER = logging.getLogger("pipeline.lipsync")


def load_config(config_path: Path | None) -> dict:
    if config_path is None:
        raise ValueError("Wav2Lip 실행을 위해 config 파일이 필요합니다.")
    if not config_path.exists():
        raise FileNotFoundError(f"설정 파일을 찾을 수 없습니다: {config_path}")
    return read_yaml(config_path)


def _build_command(config: dict, input_video: Path, input_audio: Path, output_video: Path) -> tuple[list[str], dict[str, str] | None]:
    script_path = Path(config.get("script_path", ""))
    if not script_path.exists():
        raise FileNotFoundError(f"Wav2Lip 실행 스크립트를 찾을 수 없습니다: {script_path}")

    checkpoint = Path(config.get("checkpoint", ""))
    if not checkpoint.exists():
        raise FileNotFoundError(f"Wav2Lip 체크포인트를 찾을 수 없습니다: {checkpoint}")
    face_detector = Path(config.get("face_detector", ""))

    python_exec = config.get("python_executable", sys.executable)
    bbox = config.get("bbox", [])
    nosmooth = config.get("nosmooth", False)
    resize_factor = int(config.get("resize_factor", 1) or 1)

    # clean Wav2Lip 레포의 inference.py를 직접 호출하는 경우와
    # 기존 run_wav2lip.py 스타일을 호출하는 경우를 구분한다.
    use_clean_inference = script_path.name == "inference.py"

    if use_clean_inference:
        # models_from_clean/..../wav2lip/v1/inference.py 인터페이스:
        #   --checkpoint_path, --face, --audio, --outfile
        command = [
            python_exec,
            str(script_path),
            "--checkpoint_path",
            str(checkpoint),
            "--face",
            str(input_video),
            "--audio",
            str(input_audio),
            "--outfile",
            str(output_video),
        ]
        if resize_factor != 1:
            command.extend(["--resize_factor", str(resize_factor)])
    else:
        # 기존 전용 run_wav2lip.py 스크립트와의 호환 모드
        if not face_detector.exists():
            raise FileNotFoundError(f"Face detector 파라미터를 찾을 수 없습니다: {face_detector}")

        command = [
            python_exec,
            str(script_path),
            "--checkpoint",
            str(checkpoint),
            "--face",
            str(input_video),
            "--audio",
            str(input_audio),
            "--outfile",
            str(output_video),
            "--face-detector",
            "sfd",
            "--face-detector-config",
            str(face_detector),
        ]

        if bbox:
            command.extend(["--bbox", ",".join(map(str, bbox))])

        if resize_factor != 1:
            command.extend(["--resize_factor", str(resize_factor)])

    if nosmooth:
        command.append("--nosmooth")
    if fps := config.get("fps"):
        command.extend(["--fps", str(fps)])

    env = None
    if env_config := config.get("env"):
        env = {**os.environ, **env_config}

    return command, env


def _prepare_audio_for_inference(input_audio: Path) -> Path:
    """Wav2Lip 추론용 오디오를 준비한다.

    - 입력이 이미 WAV면 그대로 사용한다.
    - 그 외(mp3 등)인 경우 ffmpeg로 ROOT_DIR/temp 아래에 WAV로 변환한다.
    """

    suffix = input_audio.suffix.lower()
    if suffix == ".wav":
        return input_audio

    temp_dir = ROOT_DIR / "temp"
    temp_dir.mkdir(parents=True, exist_ok=True)
    wav_path = temp_dir / f"{input_audio.stem}.wav"

    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(input_audio),
        str(wav_path),
    ]
    LOGGER.info("ffmpeg로 오디오를 WAV로 변환: %s", " ".join(cmd))

    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as exc:  # pragma: no cover - 외부 툴 오류
        LOGGER.error("ffmpeg 변환 실패: %s", exc)
        raise RuntimeError("ffmpeg를 사용한 오디오 변환 중 오류가 발생했습니다.") from exc

    if not wav_path.exists():
        raise RuntimeError(f"ffmpeg 변환 후 WAV 파일이 생성되지 않았습니다: {wav_path}")

    return wav_path


def _trim_media(input_video: Path, input_audio: Path, max_duration: float) -> tuple[Path, Path]:
    """지정된 길이(max_duration초)까지만 사용하는 비디오/오디오 임시 파일을 생성한다.

    ffmpeg 호출에 실패하면 원본 경로를 그대로 반환한다.
    """

    if max_duration <= 0:
        return input_video, input_audio

    temp_dir = ROOT_DIR / "temp"
    temp_dir.mkdir(parents=True, exist_ok=True)

    video_trim = temp_dir / f"{input_video.stem}_head{int(max_duration)}s{input_video.suffix}"
    audio_trim = temp_dir / f"{input_audio.stem}_head{int(max_duration)}s{input_audio.suffix}"

    # 비디오 앞부분 자르기
    cmd_video = [
        "ffmpeg",
        "-y",
        "-i",
        str(input_video),
        "-t",
        str(max_duration),
        "-c",
        "copy",
        str(video_trim),
    ]
    LOGGER.info("ffmpeg로 비디오 앞부분 잘라내기: %s", " ".join(cmd_video))
    try:
        subprocess.run(cmd_video, check=True)
    except subprocess.CalledProcessError as exc:
        LOGGER.error("ffmpeg 비디오 트림 실패: %s", exc)
        video_trim = input_video

    # 오디오 앞부분 자르기
    cmd_audio = [
        "ffmpeg",
        "-y",
        "-i",
        str(input_audio),
        "-t",
        str(max_duration),
        "-c",
        "copy",
        str(audio_trim),
    ]
    LOGGER.info("ffmpeg로 오디오 앞부분 잘라내기: %s", " ".join(cmd_audio))
    try:
        subprocess.run(cmd_audio, check=True)
    except subprocess.CalledProcessError as exc:
        LOGGER.error("ffmpeg 오디오 트림 실패: %s", exc)
        audio_trim = input_audio

    return video_trim, audio_trim


def apply_lipsync(input_video: Path, input_audio: Path, output_video: Path, config: dict) -> None:
    if not input_video.exists():
        raise FileNotFoundError(f"입력 비디오를 찾을 수 없습니다: {input_video}")
    if not input_audio.exists():
        raise FileNotFoundError(f"입력 오디오를 찾을 수 없습니다: {input_audio}")

    # inference.py 내부의 ffmpeg 호출은 경로 인용 문제로 실패할 수 있으므로,
    # 여기서 먼저 안전하게 WAV로 변환한 뒤 해당 경로를 넘긴다.
    audio_for_inference = _prepare_audio_for_inference(input_audio)

    # 설정에 max_duration_sec가 지정된 경우, 앞부분 N초만 사용하는 트림 버전을 생성한다.
    max_duration = float(config.get("max_duration_sec", 0) or 0)
    video_for_inference, audio_for_inference = _trim_media(input_video, audio_for_inference, max_duration)

    ensure_parent(output_video)
    command, env = _build_command(config, video_for_inference, audio_for_inference, output_video)

    LOGGER.info("Wav2Lip 실행: %s", " ".join(command))

    try:
        subprocess.run(command, check=True, env=env)
    except subprocess.CalledProcessError as exc:
        LOGGER.error("Wav2Lip 실행 실패: %s", exc)
        raise RuntimeError("Wav2Lip 실행 중 오류가 발생했습니다.") from exc

    if not output_video.exists():
        raise RuntimeError("Wav2Lip 실행 후 출력 영상이 생성되지 않았습니다.")

    LOGGER.info("립싱크 합성 완료: %s", output_video)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--video", required=True)
    parser.add_argument("--audio", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--config")
    args = parser.parse_args()

    logging_config = ROOT_DIR / "shared" / "logging_config.yaml"
    configure_logging(logging_config)

    config_path = Path(args.config) if args.config else None
    config = load_config(config_path)
    apply_lipsync(Path(args.video), Path(args.audio), Path(args.output), config)


if __name__ == "__main__":
    main()
