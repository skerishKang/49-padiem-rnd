from __future__ import annotations

import argparse
import shutil
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="VAD stub (pass-through copy).")
    parser.add_argument("--input", required=True, help="입력 오디오 경로")
    parser.add_argument("--output", required=True, help="출력 오디오 경로")
    args = parser.parse_args()

    src = Path(args.input)
    dst = Path(args.output)
    dst.parent.mkdir(parents=True, exist_ok=True)

    # 실제 VAD 필터링 대신 입력을 그대로 복사하여 파이프라인 흐름 유지
    shutil.copy(src, dst)
    print(f"[VAD Stub] copied input -> {dst}")


if __name__ == "__main__":
    main()
