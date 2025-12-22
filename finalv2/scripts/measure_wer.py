import argparse
import json
from pathlib import Path


def levenshtein_distance(ref_tokens: list[str], hyp_tokens: list[str]) -> int:
    m = len(ref_tokens)
    n = len(hyp_tokens)

    dp = list(range(n + 1))
    for i in range(1, m + 1):
        prev = dp[0]
        dp[0] = i
        for j in range(1, n + 1):
            cur = dp[j]
            cost = 0 if ref_tokens[i - 1] == hyp_tokens[j - 1] else 1
            dp[j] = min(dp[j] + 1, dp[j - 1] + 1, prev + cost)
            prev = cur
    return dp[n]


def tokenize(text: str) -> list[str]:
    return text.lstrip("\ufeff").split()


def load_pairs(pairs_file: Path) -> list[dict]:
    pairs: list[dict] = []
    for line in pairs_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        pairs.append(json.loads(line))
    return pairs


def write_output(result: dict, output_path: str) -> None:
    if output_path == "-":
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="WER 측정")
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
        ref_text = pair["ref"]
        hyp_text = pair["hyp"]

        ref_tokens = tokenize(ref_text)
        hyp_tokens = tokenize(hyp_text)

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
    }

    write_output(result, args.output)


if __name__ == "__main__":
    main()
