import argparse
import json
import math
from pathlib import Path


def tokenize(text: str) -> list[str]:
    return text.lstrip("\ufeff").split()


def ngrams(tokens: list[str], n: int) -> list[tuple[str, ...]]:
    return [tuple(tokens[i : i + n]) for i in range(len(tokens) - n + 1)]


def modified_precision(ref_tokens: list[str], hyp_tokens: list[str], n: int) -> tuple[int, int]:
    ref_ngrams = ngrams(ref_tokens, n)
    hyp_ngrams = ngrams(hyp_tokens, n)

    ref_counts: dict[tuple[str, ...], int] = {}
    for ng in ref_ngrams:
        ref_counts[ng] = ref_counts.get(ng, 0) + 1

    hyp_counts: dict[tuple[str, ...], int] = {}
    for ng in hyp_ngrams:
        hyp_counts[ng] = hyp_counts.get(ng, 0) + 1

    clipped = 0
    total = len(hyp_ngrams)
    for ng, count in hyp_counts.items():
        clipped += min(count, ref_counts.get(ng, 0))

    return clipped, total


def compute_bleu(ref_tokens: list[str], hyp_tokens: list[str], max_order: int = 4) -> tuple[float, list[float]]:
    precisions: list[float] = []
    for n in range(1, max_order + 1):
        clipped, total = modified_precision(ref_tokens, hyp_tokens, n)
        precisions.append((clipped / total) if total else 0.0)

    ref_len = len(ref_tokens)
    hyp_len = len(hyp_tokens)

    if hyp_len == 0:
        bp = 0.0
    elif hyp_len > ref_len:
        bp = 1.0
    else:
        bp = math.exp(1.0 - (ref_len / hyp_len))

    if any(p == 0.0 for p in precisions):
        bleu = 0.0
    else:
        bleu = bp * math.exp(sum((1.0 / max_order) * math.log(p) for p in precisions))

    return bleu * 100.0, precisions


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="BLEU 측정")
    parser.add_argument("--pairs-file", required=True, help="입력 JSONL 페어 파일 경로")
    parser.add_argument("--output", required=True, help="출력 JSON 경로('-' 지정 시 stdout)")
    parser.add_argument("--max-order", type=int, default=4, help="BLEU n-gram 최대 차수")
    return parser.parse_args()


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


def main() -> None:
    args = parse_args()
    pairs = load_pairs(Path(args.pairs_file))

    max_order = args.max_order

    corpus_ref_len = 0
    corpus_hyp_len = 0
    corpus_clipped = [0] * max_order
    corpus_total = [0] * max_order

    details: list[dict] = []

    for idx, pair in enumerate(pairs):
        sample_id = pair.get("id") or f"sample_{idx:04d}"
        ref_tokens = tokenize(pair["ref"])
        hyp_tokens = tokenize(pair["hyp"])

        corpus_ref_len += len(ref_tokens)
        corpus_hyp_len += len(hyp_tokens)

        for n in range(1, max_order + 1):
            clipped, total = modified_precision(ref_tokens, hyp_tokens, n)
            corpus_clipped[n - 1] += clipped
            corpus_total[n - 1] += total

        sentence_bleu, _ = compute_bleu(ref_tokens, hyp_tokens, max_order=max_order)

        details.append(
            {
                "id": sample_id,
                "ref_len": len(ref_tokens),
                "hyp_len": len(hyp_tokens),
                "sentence_bleu": round(sentence_bleu, 2),
            }
        )

    precisions: list[float] = []
    for i in range(max_order):
        if corpus_total[i] == 0:
            precisions.append(0.0)
        else:
            precisions.append(corpus_clipped[i] / corpus_total[i])

    if corpus_hyp_len == 0:
        bp = 0.0
    elif corpus_hyp_len > corpus_ref_len:
        bp = 1.0
    else:
        bp = math.exp(1.0 - (corpus_ref_len / corpus_hyp_len))

    if any(p == 0.0 for p in precisions):
        bleu_score = 0.0
    else:
        bleu_score = bp * math.exp(sum((1.0 / max_order) * math.log(p) for p in precisions))
        bleu_score *= 100.0

    result = {
        "metric": "BLEU",
        "sample_count": len(details),
        "bleu_score": round(bleu_score, 2),
        "max_order": max_order,
        "corpus_ref_len": corpus_ref_len,
        "corpus_hyp_len": corpus_hyp_len,
        "precisions": [round(p, 6) for p in precisions],
        "details": details,
    }

    write_output(result, args.output)


if __name__ == "__main__":
    main()
