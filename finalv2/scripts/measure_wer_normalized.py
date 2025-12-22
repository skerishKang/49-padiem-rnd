import argparse
import re
from pathlib import Path

from measure_wer import levenshtein_distance, load_pairs, write_output


def normalize_text(text: str) -> str:
    text = text.lstrip("\ufeff").lower()
    text = re.sub(r"[\.,!?]", "", text)
    return text


def tokenize_normalized(text: str) -> list[str]:
    return normalize_text(text).split()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="WER 측정(정규화: 구두점 제거 + 소문자화)")
    parser.add_argument("--pairs-file", required=True, help="입력 JSONL 페어 파일 경로")
    parser.add_argument("--output", required=True, help="출력 JSON 경로('-' 지정 시 stdout)")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    pairs_file = Path(args.pairs_file)

    pairs = load_pairs(pairs_file)

    details: list[dict] = []
    total_ref_tokens = 0
    total_errors = 0

    for idx, pair in enumerate(pairs):
        sample_id = pair.get("id") or f"sample_{idx:04d}"
        ref_tokens = tokenize_normalized(pair["ref"])
        hyp_tokens = tokenize_normalized(pair["hyp"])

        errors = levenshtein_distance(ref_tokens, hyp_tokens)
        ref_len = len(ref_tokens)
        hyp_len = len(hyp_tokens)
        wer_percent = round((errors / ref_len * 100) if ref_len else 0.0, 3)

        details.append(
            {
                "id": sample_id,
                "ref_len": ref_len,
                "hyp_len": hyp_len,
                "errors": errors,
                "wer_percent": wer_percent,
            }
        )

        total_ref_tokens += ref_len
        total_errors += errors

    wer_percent_avg = round((total_errors / total_ref_tokens * 100) if total_ref_tokens else 0.0, 3)
    wer_percent_min = min((d["wer_percent"] for d in details), default=0.0)
    wer_percent_max = max((d["wer_percent"] for d in details), default=0.0)

    result = {
        "metric": "WER",
        "sample_count": len(details),
        "wer_percent_avg": wer_percent_avg,
        "wer_percent_min": wer_percent_min,
        "wer_percent_max": wer_percent_max,
        "total_ref_tokens": total_ref_tokens,
        "total_errors": total_errors,
        "details": details,
        "normalized": True,
        "note": "구두점(.,!?) 제거 + 소문자화 후 계산된 WER",
    }

    write_output(result, args.output)


if __name__ == "__main__":
    main()
