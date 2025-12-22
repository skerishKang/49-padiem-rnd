import argparse
import json
import math
from pathlib import Path

import cv2
import numpy as np


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="PSNR/FID 측정")
    parser.add_argument("--pairs-file", required=True, help="입력 페어 JSON 경로")
    parser.add_argument("--output", required=True, help="출력 JSON 경로('-' 지정 시 stdout)")
    parser.add_argument("--max-frames", type=int, default=0, help="비디오 당 최대 프레임 수(0이면 전체)")
    return parser.parse_args()


def load_pairs(pairs_file: Path) -> list[dict]:
    data = json.loads(pairs_file.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("pairs-file은 JSON 배열이어야 합니다.")
    return data


def write_output(result: dict, output_path: str) -> None:
    if output_path == "-":
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")


def compute_video_mse(ref_path: Path, gen_path: Path, max_frames: int = 0) -> tuple[float, int]:
    ref_cap = cv2.VideoCapture(str(ref_path))
    gen_cap = cv2.VideoCapture(str(gen_path))

    if not ref_cap.isOpened():
        raise RuntimeError(f"ref 비디오를 열 수 없습니다: {ref_path}")
    if not gen_cap.isOpened():
        raise RuntimeError(f"gen 비디오를 열 수 없습니다: {gen_path}")

    frame_count = 0
    mse_sum = 0.0

    try:
        while True:
            if max_frames and frame_count >= max_frames:
                break

            ret1, f1 = ref_cap.read()
            ret2, f2 = gen_cap.read()

            if not ret1 or not ret2:
                break

            if f1.shape != f2.shape:
                f2 = cv2.resize(f2, (f1.shape[1], f1.shape[0]), interpolation=cv2.INTER_LINEAR)

            diff = f1.astype(np.float32) - f2.astype(np.float32)
            mse = float(np.mean(diff * diff))
            mse_sum += mse
            frame_count += 1

        if frame_count == 0:
            return 0.0, 0

        return mse_sum / frame_count, frame_count
    finally:
        ref_cap.release()
        gen_cap.release()


def mse_to_psnr_db(mse: float, max_pixel: float = 255.0) -> float:
    if mse <= 0.0:
        return float("inf")
    return 10.0 * math.log10((max_pixel * max_pixel) / mse)


def main() -> None:
    args = parse_args()
    pairs = load_pairs(Path(args.pairs_file))

    details: list[dict] = []
    psnr_values: list[float] = []

    for idx, pair in enumerate(pairs):
        sample_id = pair.get("id") or f"sample_{idx:04d}"
        ref_path = Path(pair["ref"])
        gen_path = Path(pair["gen"])

        mse, frames = compute_video_mse(ref_path, gen_path, max_frames=args.max_frames)
        psnr_db = mse_to_psnr_db(mse)

        details.append(
            {
                "id": sample_id,
                "ref": str(ref_path),
                "gen": str(gen_path),
                "psnr_db": psnr_db,
                "frames": frames,
                "mse": round(mse, 6),
            }
        )
        psnr_values.append(psnr_db)

    psnr_avg_db = float(np.mean(psnr_values)) if psnr_values else 0.0
    psnr_min_db = float(np.min(psnr_values)) if psnr_values else 0.0
    psnr_max_db = float(np.max(psnr_values)) if psnr_values else 0.0

    result = {
        "metric": "PSNR_FID",
        "sample_count": len(details),
        "psnr_avg_db": psnr_avg_db,
        "psnr_min_db": psnr_min_db,
        "psnr_max_db": psnr_max_db,
        "fid_score": None,
        "details": details,
    }

    write_output(result, args.output)


if __name__ == "__main__":
    main()
