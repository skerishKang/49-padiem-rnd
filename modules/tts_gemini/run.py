import argparse
import json
import os
import sys
from pathlib import Path
import base64
import struct
import google.generativeai as genai

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def _pcm_to_wav(pcm_bytes: bytes, sample_rate: int = 24000, num_channels: int = 1, bits_per_sample: int = 16) -> bytes:
    """Gemini TTS가 반환하는 16bit PCM 데이터를 WAV 컨테이너로 감싼다.

    gemini-dub-live-interpret/audioUtils.ts 의 pcmToWav 구현을 Python으로 옮긴 것.
    기본 값은 24kHz, mono, 16bit.
    """
    data_size = len(pcm_bytes)
    byte_rate = sample_rate * num_channels * bits_per_sample // 8
    block_align = num_channels * bits_per_sample // 8

    # RIFF 헤더(44바이트) 작성
    header = bytearray(44)
    # ChunkID 'RIFF'
    header[0:4] = b"RIFF"
    # ChunkSize = 36 + Subchunk2Size
    struct.pack_into("<I", header, 4, 36 + data_size)
    # Format 'WAVE'
    header[8:12] = b"WAVE"

    # Subchunk1ID 'fmt '
    header[12:16] = b"fmt "
    # Subchunk1Size (16 for PCM)
    struct.pack_into("<I", header, 16, 16)
    # AudioFormat (1 = PCM)
    struct.pack_into("<H", header, 20, 1)
    # NumChannels
    struct.pack_into("<H", header, 22, num_channels)
    # SampleRate
    struct.pack_into("<I", header, 24, sample_rate)
    # ByteRate
    struct.pack_into("<I", header, 28, byte_rate)
    # BlockAlign
    struct.pack_into("<H", header, 32, block_align)
    # BitsPerSample
    struct.pack_into("<H", header, 34, bits_per_sample)

    # Subchunk2ID 'data'
    header[36:40] = b"data"
    # Subchunk2Size
    struct.pack_into("<I", header, 40, data_size)

    return bytes(header) + pcm_bytes

def synthesize_speech(input_path: str, output_path: str, config_path: str = None):
    """
    Synthesize speech using Gemini TTS (High-Speed Mode Logic).
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in environment variables.")

    genai.configure(api_key=api_key)

    # Load input JSON
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")

    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # text_processor 출력은 {"segments": [...]} 구조, 일부 STT Gemini 출력은 리스트 루트일 수 있음
    if isinstance(data, dict):
        segments = data.get("segments", [])
    elif isinstance(data, list):
        segments = data
    else:
        segments = []

    # Combine translated/processed text for TTS
    # 우선순위: processed_text -> translated -> text
    full_text = " ".join([
        (seg.get("processed_text")
         or seg.get("translated")
         or seg.get("text", ""))
        for seg in segments
    ])

    if not full_text.strip():
        print("No text to synthesize.")
        return

    # Load config if provided
    voice_name = "Puck" # Default from geminiService.ts
    if config_path and os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
            voice_name = config.get("voice_name", "Puck")

    print(f"Synthesizing text: {full_text[:50]}...")
    print(f"Using voice: {voice_name}")

    # google-generativeai SDK를 사용하여 Gemini TTS 호출
    # Model name confirmed to work for TTS
    model_name = "gemini-2.5-flash-preview-tts" 
    model = genai.GenerativeModel(model_name)

    try:
        # Dictionary-based configuration (verified working with google-generativeai >= 0.8.5)
        generation_config = {
            "response_modalities": ["AUDIO"],
            "speech_config": {
                "voice_config": {
                    "prebuilt_voice_config": {
                        "voice_name": voice_name
                    }
                }
            }
        }

        # `contents` 에는 합성할 텍스트만 전달합니다.
        response = model.generate_content(
            contents=full_text,
            generation_config=generation_config
        )

        # Check for audio data in response parts (standard for gemini-2.5-flash-preview-tts)
        pcm_bytes = None
        if hasattr(response, 'parts'):
            for part in response.parts:
                if part.inline_data:
                    pcm_bytes = part.inline_data.data
                    break
        
        # Fallback check for response.audio (older SDK behavior)
        if not pcm_bytes and hasattr(response, 'audio') and response.audio:
             pcm_bytes = response.audio.data

        if not pcm_bytes:
            print("No audio data returned from Gemini.")
            # Debug: print response structure if needed
            # print(response)
            sys.exit(1)

        # SDK는 response.audio.data 필드에 PCM 바이너리를 직접 반환합니다.
        # pcm_bytes is already retrieved above

        # PCM 데이터를 WAV 컨테이너로 감쌉니다.
        wav_bytes = _pcm_to_wav(pcm_bytes, sample_rate=24000)

        with open(output_path, "wb") as f:
            f.write(wav_bytes)
        print(f"Successfully saved audio to {output_path}")

    except Exception as e:
        print(f"An error occurred: {str(e)}")
        # Fallback or detailed error handling could go here
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="Input JSON file path (segments)")
    parser.add_argument("--output", required=True, help="Output Audio file path")
    parser.add_argument("--config", help="Config JSON file path")
    args = parser.parse_args()

    synthesize_speech(args.input, args.output, args.config)
