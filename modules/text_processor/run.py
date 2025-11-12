from __future__ import annotations

import argparse
import logging
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Iterable


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


def process_text(input_json: Path, output_json: Path, config: dict) -> None:
    if not input_json.exists():
        raise FileNotFoundError(f"입력 JSON을 찾을 수 없습니다: {input_json}")

    LOGGER.info("텍스트 처리 시작: %s", input_json)
    data = read_json(input_json)

    operations = config.get("operations", DEFAULT_OPERATIONS)
    translation_map: dict[str, str] = config.get("translation_map", {})

    segments = data.get("segments", [])
    processed_segments = []
    for idx, segment in enumerate(segments):
        original_text = segment.get("text", "")
        translated = translation_map.get(original_text, original_text)
        processed_text = apply_operations(translated, operations)
        processed_segments.append(
            {
                "id": segment.get("id", idx),
                "original_text": original_text,
                "processed_text": processed_text,
                "start": segment.get("start", 0.0),
                "end": segment.get("end", 0.0),
            }
        )

    result = {
        "id": data.get("id", input_json.stem),
        "processed_at": datetime.utcnow().isoformat() + "Z",
        "segments": processed_segments,
        "metadata": {
            "operation_sequence": list(operations),
            "segment_count": len(processed_segments),
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
    args = parser.parse_args()

    logging_config = ROOT_DIR / "shared" / "logging_config.yaml"
    configure_logging(logging_config)

    config_path = Path(args.config) if args.config else None
    config = load_config(config_path)
    process_text(Path(args.input), Path(args.output), config)


if __name__ == "__main__":
    main()
