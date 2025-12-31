"""
VALL-E X CLI Wrapper for Padiem Pipeline.
This script wraps the VALL-E X inference code to allow command-line execution.
"""
import argparse
import logging
import os
import sys
from pathlib import Path

import soundfile as sf
import torch
import numpy as np

current_dir = Path(__file__).resolve().parent
# Ensure we run inside the VALL-E X directory for relative imports/assets
os.chdir(current_dir)
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))


def _import_vallex():
    try:
        from utils.generation import SAMPLE_RATE, generate_audio, preload_models
        return SAMPLE_RATE, generate_audio, preload_models
    except Exception as exc:  # noqa: BLE001
        print(
            f"Error: Could not import VALL-E X modules. "
            f"Make sure you are in the VALL-E X directory. ({exc})"
        )
        sys.exit(1)


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
LOGGER = logging.getLogger("run_vallex")


def main():
    parser = argparse.ArgumentParser(description="VALL-E X TTS CLI")
    parser.add_argument("--input-text", required=True, help="Path to text file containing input text")
    parser.add_argument("--output-path", required=True, help="Path to save output WAV file")
    parser.add_argument("--checkpoint-dir", default="./checkpoints", help="Directory containing checkpoints")
    parser.add_argument("--speaker", default=None, help="Speaker prompt name (optional)")
    parser.add_argument("--language", default="auto", help="Language (auto, en, zh, ja, ko)")
    
    args = parser.parse_args()

    input_text_path = Path(args.input_text).resolve()
    output_path = Path(args.output_path).resolve()
    checkpoint_dir = Path(args.checkpoint_dir).resolve()

    if not input_text_path.exists():
        LOGGER.error(f"Input text file not found: {input_text_path}")
        sys.exit(1)

    text = input_text_path.read_text(encoding="utf-8").strip()
    if not text:
        LOGGER.error("Input text is empty")
        sys.exit(1)

    LOGGER.info(f"Loading models from {checkpoint_dir}...")
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    LOGGER.info(f"Synthesizing text: {text[:50]}...")

    SAMPLE_RATE, generate_audio, preload_models = _import_vallex()

    # Configure checkpoints directory for generation module
    try:
        import utils.generation as gen_module
        gen_module.checkpoints_dir = str(checkpoint_dir)
    except Exception:
        pass

    preload_models()

    prompt_arg = args.speaker
    if prompt_arg and prompt_arg.lower() == "default":
        prompt_arg = None

    audio_array = generate_audio(text, prompt=prompt_arg, language=args.language)

    if audio_array is None:
        LOGGER.error("Audio generation failed (returned None)")
        sys.exit(1)

    # Save to file
    # VALL-E X usually returns numpy array. Sample rate is 24000 by default.
    LOGGER.info(f"Saving audio to {output_path}")
    sf.write(str(output_path), audio_array, SAMPLE_RATE)
    LOGGER.info("Done.")


if __name__ == "__main__":
    main()
