from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path
from typing import Optional

import re
import torch


ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from shared.utils.io_helpers import (
    configure_logging,
    ensure_parent,
    read_json,
    read_yaml,
)


LOGGER = logging.getLogger("pipeline.tts.xtts")


def load_config(config_path: Path | None) -> dict:
    if config_path is None:
        raise ValueError("XTTS 합성을 위해 config 파일이 필요합니다.")
    if not config_path.exists():
        raise FileNotFoundError(f"설정 파일을 찾을 수 없습니다: {config_path}")
    return read_yaml(config_path)


def _normalize_for_tts(text: str) -> str:
    """TTS용 텍스트 정규화.

    - 음절 맞추기용 하이픈(ex-cep-tion)을 제거해 자연스럽게 읽도록 한다.
    """
    if not text:
        return ""
    return re.sub(r"\s*-\s*", "", text)


def _prepare_text(input_json: Path, fallback_text: str | None = None) -> str:
    data = read_json(input_json)
    segments = data.get("segments", [])
    raw_texts = [segment.get("processed_text") or segment.get("text", "") for segment in segments]
    texts = [_normalize_for_tts(t) for t in raw_texts]
    combined = " ".join(filter(None, texts)).strip()
    if not combined and fallback_text:
        combined = fallback_text
    if not combined:
        raise ValueError("합성할 텍스트가 비어 있습니다.")
    return combined


def _patch_transformers() -> None:
    """Ensure BeamSearchScorer is available for Coqui XTTS on newer transformers."""
    try:
        import transformers  # type: ignore
    except Exception as exc:  # pragma: no cover
        LOGGER.warning("transformers 임포트에 실패했습니다: %s", exc)
        return

    # Already present
    if hasattr(transformers, "BeamSearchScorer"):
        return

    # Try public generation module
    try:
        from transformers.generation import BeamSearchScorer  # type: ignore
        transformers.BeamSearchScorer = BeamSearchScorer  # type: ignore[attr-defined]
        LOGGER.info("Patched transformers.BeamSearchScorer for XTTS compatibility.")
        return
    except Exception:
        pass

    # Try internal module (transformers>=4.46)
    try:
        from importlib import import_module

        beam_mod = import_module("transformers.generation.beam_search")
        BeamSearchScorer = getattr(beam_mod, "BeamSearchScorer", None)
        if BeamSearchScorer is None:
            beam_mod = import_module("transformers.generation._internal.beam_search")
            BeamSearchScorer = getattr(beam_mod, "BeamSearchScorer")
        transformers.BeamSearchScorer = BeamSearchScorer  # type: ignore[attr-defined]
        LOGGER.info("Patched transformers.BeamSearchScorer from internal module for XTTS.")
    except Exception as exc:  # pragma: no cover - defensive
        LOGGER.warning("Failed to patch transformers for XTTS: %s", exc)
        # Last-resort stub to satisfy import site even if functionality is limited
        class _DummyBeamSearchScorer:  # pragma: no cover - fallback only
            def __init__(self, *args, **kwargs):  # noqa: D401
                """Compatibility stub for BeamSearchScorer."""
                self.args = args
                self.kwargs = kwargs
        transformers.BeamSearchScorer = _DummyBeamSearchScorer  # type: ignore[attr-defined]

    # Ensure import-style lookup also succeeds
    try:
        from transformers import BeamSearchScorer as _probe  # type: ignore  # noqa: F401
    except Exception as exc:  # pragma: no cover - defensive
        LOGGER.warning("Direct import of BeamSearchScorer still failing after patch: %s", exc)


def _load_tts_model(config: dict) -> TTS:
    _patch_transformers()
    from TTS.api import TTS  # import after patching to avoid import errors

    model_name = config.get("model_name", "tts_models/multilingual/multi-dataset/xtts_v2")
    use_gpu = config.get("use_gpu", True)
    
    if use_gpu and not torch.cuda.is_available():
        LOGGER.warning("CUDA를 사용할 수 없습니다. CPU 모드로 전환합니다.")
        use_gpu = False

    LOGGER.info("XTTS 모델 로드: %s (GPU=%s)", model_name, use_gpu)
    return TTS(model_name=model_name, progress_bar=False, gpu=use_gpu)


def _convert_to_wav(input_path: Path) -> Path:
    """Convert audio to WAV using ffmpeg if it's not already WAV."""
    if input_path.suffix.lower() == ".wav":
        return input_path
        
    LOGGER.info(f"오디오 변환 시작 (ffmpeg): {input_path} -> wav")
    output_path = input_path.with_suffix(".converted.wav")
    
    # 이미 변환된 파일이 있으면 재사용
    if output_path.exists():
        return output_path

    try:
        import subprocess
        command = [
            "ffmpeg", "-y",
            "-i", str(input_path),
            "-ar", "22050", # XTTS usually works well with 22050 or 24000
            "-ac", "1",     # Mono is usually sufficient for reference
            str(output_path)
        ]
        subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        LOGGER.info(f"오디오 변환 완료: {output_path}")
        return output_path
    except Exception as e:
        LOGGER.error(f"오디오 변환 실패: {e}")
        return input_path # 실패 시 원본 반환 (운에 맡김)


def _resolve_speaker_wav(config: dict) -> Optional[str]:
    speaker_wav = config.get("speaker_wav")
    if speaker_wav:
        # Convert to wav if needed (ffmpeg)
        wav_path = _convert_to_wav(Path(speaker_wav))
        if not wav_path.exists():
            raise FileNotFoundError(f"스피커 참조 음성을 찾을 수 없습니다: {wav_path}")
        return str(wav_path)
    return None


def synthesize_backup(input_json: Path, output_audio: Path, config: dict) -> None:
    if not input_json.exists():
        raise FileNotFoundError(f"입력 JSON을 찾을 수 없습니다: {input_json}")

    LOGGER.info("XTTS 백업 합성을 시작합니다: %s", input_json)
    text = _prepare_text(input_json, config.get("fallback_text"))
    speaker_wav = _resolve_speaker_wav(config)

    tts = _load_tts_model(config)

    ensure_parent(output_audio)
    synthesis_kwargs = {
        "text": text,
        "file_path": str(output_audio),
    }
    if speaker_wav:
        synthesis_kwargs["speaker_wav"] = speaker_wav
    if language := config.get("language"):
        synthesis_kwargs["language"] = language

    try:
        tts.tts_to_file(**synthesis_kwargs)
    except Exception as exc:  # noqa: BLE001
        LOGGER.exception("XTTS 합성 실패")
        raise RuntimeError("XTTS 합성 중 오류가 발생했습니다.") from exc

    LOGGER.info("XTTS 백업 합성 완료: %s", output_audio)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--config")
    parser.add_argument("--speaker-wav")
    parser.add_argument("--language")
    args = parser.parse_args()

    logging_config = ROOT_DIR / "shared" / "logging_config.yaml"
    configure_logging(logging_config)

    config_path = Path(args.config) if args.config else None
    if config_path is None:
        default_config = ROOT_DIR / "modules" / "tts_xtts" / "config" / "settings.yaml"
        if default_config.exists():
            config_path = default_config
            LOGGER.info(f"설정 파일이 제공되지 않아 기본 설정을 사용합니다: {config_path}")

    config = load_config(config_path)
    
    # Command line argument overrides config
    if args.speaker_wav:
        config["speaker_wav"] = args.speaker_wav
    if args.language:
        config["language"] = args.language

    synthesize_backup(Path(args.input), Path(args.output), config)


if __name__ == "__main__":
    main()
