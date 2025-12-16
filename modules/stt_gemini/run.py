import argparse
import json
import os
import sys
from pathlib import Path

import google.generativeai as genai
from dotenv import load_dotenv


# Load environment variables
load_dotenv()


def _guess_mime_type(path: str) -> str:
    """간단한 확장자 기반 MIME 타입 추론 (오디오 용도)."""
    suffix = Path(path).suffix.lower()
    if suffix == ".wav":
        return "audio/wav"
    if suffix == ".mp3":
        return "audio/mpeg"
    if suffix in {".m4a", ".aac"}:
        return "audio/mp4"
    if suffix == ".flac":
        return "audio/flac"
    # 기본값
    return "audio/wav"


def process_audio(input_path: str, output_path: str, config_path: str | None = None) -> None:
    """
    Process audio using Gemini 1.5 Pro for STT, Translation, and Syllable Matching.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in environment variables.")

    genai.configure(api_key=api_key)

    # Check for transcribe_only flag
    transcribe_only = False
    target_lang = "Korean"
    input_lang = "auto"
    
    if config_path and os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
            target_lang = config.get("target_language", "Korean")
            input_lang = config.get("source_language", "auto")
            transcribe_only = config.get("transcribe_only", False)

    # 오디오 파일을 Gemini로 업로드하지 않고, 바이트로 읽어 Part로 전달한다.
    # (google.generativeai의 upload_file는 최신 SDK에서 제거되었기 때문에 사용하지 않음)
    print(f"Loading audio file: {input_path}")
    mime_type = _guess_mime_type(input_path)
    with open(input_path, "rb") as f:
        audio_bytes = f.read()

    audio_part = {
        "mime_type": mime_type,
        "data": audio_bytes,
    }

    # Construct Prompt
    if transcribe_only:
        prompt = f"""
        Analyze the audio. 
        1. Transcribe the speech.
        2. Break it down into logical segments based on pauses or sentences.
        3. Provide a timestamp for start and end of each segment.
        
        Return ONLY JSON with the following schema:
        [
          {{
            "id": "segment_id",
            "startTime": "HH:MM:SS.mmm",
            "endTime": "HH:MM:SS.mmm",
            "originalText": "original transcription",
            "translatedText": "original transcription" 
          }}
        ]
        """
    else:
        prompt = f"""
        Analyze the audio. 
        1. Transcribe the speech.
        2. Translate the speech from {input_lang if input_lang != 'auto' else 'detected language'} to {target_lang}.
        3. CRITICAL: The translation MUST attempt to match the approximate syllable count and rhythm of the original speech for dubbing purposes.
        4. Break it down into logical segments based on pauses or sentences.
        5. Provide a timestamp for start and end of each segment.
        
        Return ONLY JSON with the following schema:
        [
          {{
            "id": "segment_id",
            "startTime": "HH:MM:SS.mmm",
            "endTime": "HH:MM:SS.mmm",
            "originalText": "original transcription",
            "translatedText": "translated text matching syllable count"
          }}
        ]
        """

    model = genai.GenerativeModel("gemini-2.5-flash")

    print("Generating content...")
    response = model.generate_content(
        [prompt, audio_part],
        generation_config={
            "response_mime_type": "application/json",
        },
    )

    print("Processing response...")
    try:
        segments = json.loads(response.text)
        
        # Convert to project's standard JSON format
        # Project format: [{"start": 0.0, "end": 1.0, "text": "...", "translated": "..."}]
        formatted_segments = []
        
        for seg in segments:
            start_str = seg.get("startTime", "00:00:00.000")
            end_str = seg.get("endTime", "00:00:00.000")
            
            # Helper to convert time string to seconds
            def time_str_to_seconds(t_str):
                try:
                    t_str = str(t_str).strip()
                    # 콜론이 없으면 Gemini가 "309.0" 처럼 센티초로 줄 가능성이 있으므로 100으로 나눈다
                    if ':' not in t_str:
                        return float(t_str) / 100.0
                    h, m, s = t_str.split(':')
                    return int(h) * 3600 + int(m) * 60 + float(s)
                except Exception:
                    return 0.0

            start_val = time_str_to_seconds(start_str)
            end_val = time_str_to_seconds(end_str)

            # Gemini가 간혹 start > end 로 잘못 반환하는 경우가 있어 보정
            if end_val < start_val:
                start_val, end_val = end_val, start_val

            formatted_segments.append({
                "start": start_val,
                "end": end_val,
                "text": seg.get("originalText", ""),
                "translated": seg.get("translatedText", "")
            })

        # 시작 시간을 기준으로 세그먼트 정렬
        formatted_segments.sort(key=lambda s: s.get("start", 0.0))

        # Save output
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(formatted_segments, f, indent=2, ensure_ascii=False)
            
        print(f"Successfully saved to {output_path}")

    except json.JSONDecodeError:
        print("Failed to parse JSON response from Gemini.")
        print("Raw response:", response.text)
        sys.exit(1)
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="Input audio file path")
    parser.add_argument("--output", required=True, help="Output JSON file path")
    parser.add_argument("--config", help="Config JSON file path")
    args = parser.parse_args()

    process_audio(args.input, args.output, args.config)
