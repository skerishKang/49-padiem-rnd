import os
import argparse
import logging
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Iterable
import json

import unicodedata
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold


ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from shared.utils.io_helpers import (
    configure_logging,
    ensure_parent,
    read_json,
    read_yaml,
    write_json,
)


LOGGER = logging.getLogger("pipeline.text_processor")


DEFAULT_OPERATIONS = ("trim", "collapse_whitespace", "preserve_case")
DEFAULT_SYLLABLE_TOLERANCE = 0.1

VOWEL_SETS = {
    "en": "aeiouy",
    "fr": "aeiouyàâäæéèêëîïôöœùûüÿ",
    "es": "aeiouáéíóúü",
    "de": "aeiouäöüy",
    "ru": "аеёиоуыэюя",
}

LANGUAGE_CATEGORY = {
    "ko": "hangul",
    "zh": "cjk",
    "ja": "kana",
    "en": "vowel",
    "fr": "vowel",
    "es": "vowel",
    "de": "vowel",
    "ru": "vowel",
}


def load_config(config_path: Path | None) -> dict:
    if config_path is None:
        return {}
    if not config_path.exists():
        raise FileNotFoundError(f"설정 파일을 찾을 수 없습니다: {config_path}")
    return read_yaml(config_path)


def apply_operations(text: str, operations: Iterable[str]) -> str:
    processed = text
    ops = list(operations) or list(DEFAULT_OPERATIONS)
    if "trim" in ops:
        processed = processed.strip()
    if "collapse_whitespace" in ops:
        processed = re.sub(r"\s+", " ", processed)
    if "lower" in ops:
        processed = processed.lower()
    if "upper" in ops and "lower" not in ops:
        processed = processed.upper()
    return processed


def count_hangul_syllables(text: str) -> int:
    return sum(1 for ch in text if "\uAC00" <= ch <= "\uD7A3")


def count_cjk_syllables(text: str) -> int:
    return sum(1 for ch in text if "\u4e00" <= ch <= "\u9fff")


def count_kana_syllables(text: str) -> int:
    return sum(1 for ch in text if ("\u3040" <= ch <= "\u309f") or ("\u30a0" <= ch <= "\u30ff"))


def count_vowel_groups(text: str, vowels: str) -> int:
    lowered = unicodedata.normalize("NFKD", text.lower())
    count = 0
    prev_vowel = False
    for ch in lowered:
        if ch in vowels:
            if not prev_vowel:
                count += 1
            prev_vowel = True
        else:
            prev_vowel = False
    return count


def auto_detect_language(text: str) -> str:
    """단순 언어 자동 감지 - 텍스트의 문자 기반으로 언어 추정."""
    if not text:
        return "en"

    # 한글 검사 (가-힝 범위)
    hangul_count = sum(1 for ch in text if "\uAC00" <= ch <= "\uD7A3")
    if hangul_count > len(text) * 0.3:  # 30% 이상 한글
        return "ko"

    # 히라가나/가타카나 검사
    kana_count = sum(1 for ch in text if ("\u3040" <= ch <= "\u309f") or ("\u30a0" <= ch <= "\u30ff"))
    if kana_count > len(text) * 0.2:  # 20% 이상 가나
        return "ja"

    # CJK 통합 한자 검사
    cjk_count = sum(1 for ch in text if "\u4e00" <= ch <= "\u9fff")
    if cjk_count > len(text) * 0.3:  # 30% 이상 한자
        return "zh"

    # 라틴 알파벳이 주를 이루면 엔글리시
    latin_count = sum(1 for ch in text if ch.isascii() and ch.isalpha())
    if latin_count > len(text) * 0.5:  # 50% 이상 라틴 알파벳
        return "en"

    # 기본값은 영어
    return "en"


def estimate_syllables(text: str, language: str | None) -> int:
    if not text:
        return 0
    lang = (language or "en").lower()
    category = LANGUAGE_CATEGORY.get(lang, "vowel")
    if category == "hangul":
        return count_hangul_syllables(text)
    if category == "cjk":
        return count_cjk_syllables(text)
    if category == "kana":
        return count_kana_syllables(text)
    vowels = VOWEL_SETS.get(lang, VOWEL_SETS["en"])
    return count_vowel_groups(text, vowels) or 1


    return count_vowel_groups(text, vowels) or 1


def _filter_hallucinations(segments: list[dict]) -> list[dict]:
    """반복되는 환각(Hallucination) 세그먼트를 필터링하고 병합합니다."""
    if not segments:
        return []
    
    filtered = []
    last_text = ""
    repeat_count = 0
    
    for seg in segments:
        text = seg.get("text", "").strip()
        
        # 텍스트가 이전과 동일한지 확인
        if text and text == last_text:
            repeat_count += 1
        else:
            repeat_count = 0
            last_text = text
            
        # 2회 이상 반복(총 3회째 등장)되면 환각으로 간주하고 병합
        if repeat_count >= 2:
            # 이전 세그먼트의 종료 시간을 현재 세그먼트의 종료 시간으로 연장
            if filtered:
                filtered[-1]["end"] = seg.get("end")
            LOGGER.warning(f"환각 의심 세그먼트 병합됨: '{text}' ({seg.get('start')} - {seg.get('end')})")
            continue
            
        filtered.append(seg)
        
    return filtered


def _batch_translate_segments(
    model: genai.GenerativeModel,
    segments: list[dict],
    source_language: str,
    target_language: str,
    syllable_tolerance: float,
) -> dict[int, str]:
    """세그먼트 리스트를 한 번에 Gemini에 보내 배치 번역합니다.

    반환값은 segment id -> translated_text 매핑입니다.
    """
    # 입력 세그먼트에서 필요한 최소 정보만 추려서 payload 구성
    simple_segments: list[dict] = []
    for seg in segments:
        seg_id = seg.get("id")
        text = seg.get("text", "")
        if seg_id is None or not str(text).strip():
            continue
        source_syllables = estimate_syllables(text, source_language)
        simple_segments.append(
            {
                "id": seg_id,
                "text": text,
                "source_syllables": source_syllables,
            }
        )

    if not simple_segments:
        return {}

    payload = {
        "source_language": source_language,
        "target_language": target_language,
        "syllable_tolerance": syllable_tolerance,
        "segments": simple_segments,
    }

    prompt = f"""You are translating subtitle segments for dubbing.\\n\\n
Input JSON:
{json.dumps(payload, ensure_ascii=False, indent=2)}

For each item in "segments", translate the "text" from {source_language} to {target_language}.
- Try to keep the approximate syllable count close to "source_syllables" for each segment (±{int(syllable_tolerance * 100)}%).
- Preserve the meaning and tone as much as possible.

Return ONLY JSON with this structure:
{{
  "segments": [
    {{"id": <int>, "translated_text": "<translation>"}},
    ...
  ]
}}

Do not add any commentary, explanations, or extra fields.
"""

    response = model.generate_content(
        prompt,
        safety_settings={
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        },
    )

    translations: dict[int, str] = {}
    try:
        data = json.loads(response.text)
        items = data.get("segments", []) if isinstance(data, dict) else data
        for item in items:
            if not isinstance(item, dict):
                continue
            seg_id = item.get("id")
            translated = item.get("translated_text") or item.get("text")
            if seg_id is None or not translated:
                continue
            try:
                seg_id_int = int(seg_id)
            except Exception:
                continue
            translations[seg_id_int] = str(translated).strip()
    except Exception as exc:  # JSON 파싱 실패 등
        LOGGER.warning("배치 번역 결과 파싱 실패: %s", exc)

    return translations


def process_text(input_json: Path, output_json: Path, config: dict) -> None:
    if not input_json.exists():
        raise FileNotFoundError(f"입력 JSON을 찾을 수 없습니다: {input_json}")

    LOGGER.info("텍스트 처리 시작: %s", input_json)
    data = read_json(input_json)

    # STT Gemini 출력처럼 루트가 리스트인 경우 호환을 위해 래핑
    # 기대 형식: {"language": ..., "segments": [...]}
    if isinstance(data, list):
        data = {
            "segments": data,
            "language": config.get("source_language", "ko"),
        }

    operations = config.get("operations", DEFAULT_OPERATIONS)
    translation_map: dict[str, str] = config.get("translation_map", {})
    source_language = data.get("language") or config.get("source_language", "ko")
    target_language = config.get("target_language", "en")
    syllable_tolerance = float(config.get("syllable_tolerance", DEFAULT_SYLLABLE_TOLERANCE))
    enforce_timing = bool(config.get("enforce_timing", True))

    raw_segments = data.get("segments", [])
    # 환각 필터링 적용
    segments = _filter_hallucinations(raw_segments)
    if len(segments) < len(raw_segments):
        LOGGER.info(f"환각 필터링: {len(raw_segments)} -> {len(segments)} 세그먼트로 감소")

    # 일부 STT 출력(Gemini)은 id 필드가 없으므로, 이후 로직과 배치 번역에서 사용하기 위해 자동 부여
    for idx, seg in enumerate(segments):
        if "id" not in seg:
            seg["id"] = idx

    # 자동 언어 감지 로직
    detected_source_lang = None
    if not source_language or source_language in ("auto", "automatic"):
        detected_lang = data.get("language")
        if detected_lang:
            detected_source_lang = detected_lang
        else:
            detected_lang = config.get("source_language")
            if detected_lang and detected_lang not in ("auto", "automatic"):
                detected_source_lang = detected_lang
            else:
                if segments:
                    first_text = segments[0].get("text", "")
                    auto_detected = auto_detect_language(first_text)
                    detected_source_lang = auto_detected
                    LOGGER.info("원본 언어를 자동 감지했습니다: %s", auto_detected)
                else:
                    detected_source_lang = "en"

        if not source_language or source_language in ("auto", "automatic"):
            source_language = detected_source_lang

    # Gemini 번역기 초기화
    gemini_model = None
    translations: dict[int, str] = {}
    api_key = config.get("gemini_api_key") or os.getenv("GEMINI_API_KEY")

    # STT Gemini 출력처럼 세그먼트에 이미 translated 필드가 있는 경우, 이 값을 우선 사용하고
    # 추가 Gemini 번역 호출은 생략한다.
    has_inline_translated = any(
        isinstance(seg.get("translated"), str) and seg["translated"].strip()
        for seg in segments
    )

    if source_language != target_language and not has_inline_translated:
        if api_key:
            try:
                genai.configure(api_key=api_key)
                model_name = config.get("gemini_model_name", "gemini-2.5-flash-lite")
                gemini_model = genai.GenerativeModel(model_name)
                LOGGER.info("Gemini 모델 초기화: %s (%s -> %s)", model_name, source_language, target_language)

                # 세그먼트별 개별 호출 대신 배치 번역 한 번 수행
                try:
                    translations = _batch_translate_segments(
                        gemini_model,
                        segments,
                        source_language,
                        target_language,
                        syllable_tolerance,
                    )
                    LOGGER.info("배치 번역 완료: %d개 세그먼트", len(translations))
                except Exception as exc:
                    LOGGER.warning("배치 번역 실패, 원문 텍스트로 진행합니다: %s", exc)
                    translations = {}

            except Exception as exc:
                LOGGER.warning("Gemini 초기화 실패: %s", exc)
        else:
            LOGGER.warning("Gemini API Key가 설정되지 않아 번역을 건너뜁니다.")
    elif has_inline_translated:
        LOGGER.info("세그먼트에 translated 필드가 있어 Gemini 번역 호출을 생략합니다.")

    processed_segments = []
    for idx, segment in enumerate(segments):
        original_text = segment.get("text", "")
        
        # 1. Translation Map 적용
        text_to_process = translation_map.get(original_text, original_text)

        # 2. STT Gemini 등에서 세그먼트에 이미 translated 필드가 있으면 이를 우선 사용
        if has_inline_translated:
            inline = segment.get("translated")
            if isinstance(inline, str) and inline.strip():
                text_to_process = inline
        else:
            # 3. 배치 번역 결과가 있으면 사용
            seg_id = segment.get("id")
            if seg_id is not None and translations:
                translated = translations.get(int(seg_id))
                if translated:
                    text_to_process = translated

        # 3. 후처리 연산 (trim 등)
        processed_text = apply_operations(text_to_process, operations)
        
        # 4. 음절 수 및 타이밍 계산
        start = float(segment.get("start", 0.0))
        end = float(segment.get("end", 0.0))
        duration = max(end - start, 0.0)
        source_syllables = estimate_syllables(original_text, source_language)
        target_syllables = estimate_syllables(processed_text, target_language)
        ratio = target_syllables / source_syllables if source_syllables else 1.0
        needs_review = False
        notes: str | None = None
        if source_syllables and abs(ratio - 1.0) > syllable_tolerance:
            needs_review = True
            notes = f"syllable ratio {ratio:.2f} exceeds tolerance {syllable_tolerance:.2f}"
        if enforce_timing and duration > 0 and needs_review is False:
            expected_rate = source_syllables / duration if source_syllables else 0.0
            actual_rate = target_syllables / duration if duration else 0.0
            if source_syllables and abs(actual_rate - expected_rate) / expected_rate > syllable_tolerance:
                needs_review = True
                notes = "syllable rate deviates from source"

        processed_segments.append(
            {
                "id": segment.get("id", idx),
                "original_text": original_text,
                "processed_text": processed_text,
                "start": start,
                "end": end,
                "duration": duration,
                "source_language": source_language,
                "target_language": target_language,
                "source_syllables": source_syllables,
                "target_syllables": target_syllables,
                "syllable_ratio": round(ratio, 3),
                "needs_review": needs_review,
                "notes": notes,
            }
        )

    result = {
        "id": data.get("id", input_json.stem),
        "processed_at": datetime.utcnow().isoformat() + "Z",
        "segments": processed_segments,
        "metadata": {
            "operation_sequence": list(operations),
            "segment_count": len(processed_segments),
            "source_language": source_language,
            "target_language": target_language,
            "syllable_tolerance": syllable_tolerance,
            "enforce_timing": enforce_timing,
        },
    }

    ensure_parent(output_json)
    write_json(output_json, result)
    LOGGER.info("텍스트 처리 완료: %s", output_json)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--config")
    parser.add_argument("--source-language")
    parser.add_argument("--target-language")
    parser.add_argument("--gemini-api-key")
    parser.add_argument("--syllable-tolerance", type=float)
    parser.add_argument("--enforce-timing", type=str)  # "true"/"false"로 받음

    args = parser.parse_args()

    logging_config = ROOT_DIR / "shared" / "logging_config.yaml"
    configure_logging(logging_config)

    config_path = Path(args.config) if args.config else None
    config = load_config(config_path)

    if args.source_language:
        config["source_language"] = args.source_language
    if args.target_language:
        config["target_language"] = args.target_language
    if args.gemini_api_key:
        config["gemini_api_key"] = args.gemini_api_key
    if args.syllable_tolerance is not None:
        config["syllable_tolerance"] = args.syllable_tolerance
    if args.enforce_timing is not None:
        config["enforce_timing"] = args.enforce_timing.lower() == "true"

    process_text(Path(args.input), Path(args.output), config)


if __name__ == "__main__":
    main()