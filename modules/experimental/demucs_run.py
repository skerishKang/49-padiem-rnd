from __future__ import annotations

import argparse
import shutil
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Demucs experimental stub (pass-through copy).")
    parser.add_argument("--input", required=True, help="입력 오디오 경로")
    parser.add_argument("--output", required=True, help="출력 오디오 경로")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # 실제 demucs 실행 대신 입력 오디오를 그대로 복사하여 파이프라인을 이어줌.
    shutil.copy(input_path, output_path)
    print(f"[Demucs Stub] copied input -> {output_path}")


if __name__ == "__main__":
    main()
