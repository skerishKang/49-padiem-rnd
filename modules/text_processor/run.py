from __future__ import annotations

import argparse
import logging
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Iterable

import unicodedata


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


def process_text(input_json: Path, output_json: Path, config: dict) -> None:
    if not input_json.exists():
        raise FileNotFoundError(f"입력 JSON을 찾을 수 없습니다: {input_json}")

    LOGGER.info("텍스트 처리 시작: %s", input_json)
    data = read_json(input_json)

    operations = config.get("operations", DEFAULT_OPERATIONS)
    translation_map: dict[str, str] = config.get("translation_map", {})
    source_language = data.get("language") or config.get("source_language", "ko")
    target_language = config.get("target_language", "en")
    syllable_tolerance = float(config.get("syllable_tolerance", DEFAULT_SYLLABLE_TOLERANCE))
    enforce_timing = bool(config.get("enforce_timing", True))

    segments = data.get("segments", [])
    processed_segments = []
    for idx, segment in enumerate(segments):
        original_text = segment.get("text", "")
        translated = translation_map.get(original_text, original_text)
        processed_text = apply_operations(translated, operations)
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
            # 시간 대비 음절 속도도 참고용으로 기록
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
    args = parser.parse_args()

    logging_config = ROOT_DIR / "shared" / "logging_config.yaml"
    configure_logging(logging_config)

    config_path = Path(args.config) if args.config else None
    config = load_config(config_path)

    if args.source_language:
        config["source_language"] = args.source_language
    if args.target_language:
        config["target_language"] = args.target_language

    process_text(Path(args.input), Path(args.output), config)


if __name__ == "__main__":
    main()
