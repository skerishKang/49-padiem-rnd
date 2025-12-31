# -*- coding: utf-8 -*-
"""
Gemini TTS 다중 문장 생성 스크립트 (로컬 실행용)
- 의존성: pip install google-genai
- 입력 대본: script_ko_en.txt (언어,스타일,ID,텍스트)
- 출력: 최종보고서_오디오/out/{id}_{lang}_{style}.{ext}
주의: 이 스크립트는 로컬에서만 사용하고, API 키는 외부 저장소에 커밋하지 마십시오.
"""

import base64
import mimetypes
import os
import pathlib
import struct
from typing import Dict, Tuple

from google import genai
from google.genai import types

# *** 로컬 전용 하드코딩 키 ***
API_KEY = "AIzaSyA_djsQUG0np0xJ_jjSQNPKrAGrzTdGN_w"
MODEL = "gemini-2.5-flash-preview-tts"
BASE_DIR = pathlib.Path(__file__).resolve().parent
SCRIPT_PATH = BASE_DIR / "script_ko_en.txt"
OUT_DIR = BASE_DIR / "out"

# 언어/스타일별 프리셋 보이스 (필요 시 변경)
VOICE_MAP: Dict[Tuple[str, str], str] = {
    ("KO", "neutral"): "Soleil",
    ("KO", "joy"): "Jun",
    ("EN", "neutral"): "Zephyr",
    ("EN", "joy"): "Puck",
}


def save_binary_file(file_path: pathlib.Path, data: bytes) -> None:
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_bytes(data)
    print(f"[saved] {file_path}")


def parse_script(path: pathlib.Path):
    lines = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        raw = raw.strip()
        if not raw or raw.startswith("#"):
            continue
        parts = raw.split(",", 3)
        if len(parts) != 4:
            print(f"[skip] malformed line: {raw}")
            continue
        lang, style, sample_id, text = [p.strip() for p in parts]
        lines.append((lang, style, sample_id, text))
    return lines


def convert_to_wav(audio_data: bytes, mime_type: str) -> bytes:
    """MIME 정보 기반으로 WAV 헤더를 붙여 PCM으로 변환."""
    params = parse_audio_mime_type(mime_type)
    bits_per_sample = params["bits_per_sample"] or 16
    sample_rate = params["rate"] or 24000
    num_channels = 1
    data_size = len(audio_data)
    bytes_per_sample = bits_per_sample // 8
    block_align = num_channels * bytes_per_sample
    byte_rate = sample_rate * block_align
    chunk_size = 36 + data_size

    header = struct.pack(
        "<4sI4s4sIHHIIHH4sI",
        b"RIFF",
        chunk_size,
        b"WAVE",
        b"fmt ",
        16,
        1,
        num_channels,
        sample_rate,
        byte_rate,
        block_align,
        bits_per_sample,
        b"data",
        data_size,
    )
    return header + audio_data


def parse_audio_mime_type(mime_type: str):
    bits_per_sample = 16
    rate = 24000
    parts = mime_type.split(";")
    for param in parts:
        p = param.strip().lower()
        if p.startswith("rate="):
            try:
                rate = int(p.split("=", 1)[1])
            except (ValueError, IndexError):
                pass
        if "audio/l" in p:
            try:
                bits_per_sample = int(p.split("l", 1)[1])
            except (ValueError, IndexError):
                pass
    return {"bits_per_sample": bits_per_sample, "rate": rate}


def pick_voice(lang: str, style: str) -> str:
    return VOICE_MAP.get((lang, style), "Zephyr")


def generate_for_line(client, lang: str, style: str, sample_id: str, text: str):
    voice_name = pick_voice(lang, style)
    contents = [types.Content(role="user", parts=[types.Part.from_text(text=text)])]
    cfg = types.GenerateContentConfig(
        temperature=1,
        response_modalities=["audio"],
        speech_config=types.SpeechConfig(
            voice_config=types.VoiceConfig(
                prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=voice_name)
            )
        ),
    )

    idx = 0
    for chunk in client.models.generate_content_stream(
        model=MODEL,
        contents=contents,
        config=cfg,
    ):
        if not chunk.candidates or not chunk.candidates[0].content:
            continue
        parts = chunk.candidates[0].content.parts or []
        if not parts:
            continue
        inline = parts[0].inline_data
        if not inline or not inline.data:
            continue
        data = inline.data
        ext = mimetypes.guess_extension(inline.mime_type) or ".wav"
        if ext == ".wav":
            out_bytes = data
        else:
            out_bytes = convert_to_wav(data, inline.mime_type)
            ext = ".wav"
        out_path = OUT_DIR / f"{sample_id}_{lang.lower()}_{style}_{idx}{ext}"
        save_binary_file(out_path, out_bytes)
        idx += 1


def main():
    if not API_KEY:
        raise SystemExit("GEMINI_API_KEY가 설정되지 않았습니다.")
    client = genai.Client(api_key=API_KEY)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    lines = parse_script(SCRIPT_PATH)
    if not lines:
        raise SystemExit("대본이 비어 있습니다: script_ko_en.txt")
    for lang, style, sample_id, text in lines:
        print(f"[gen] {sample_id} ({lang}/{style}) -> {text}")
        generate_for_line(client, lang, style, sample_id, text)


if __name__ == "__main__":
    main()
