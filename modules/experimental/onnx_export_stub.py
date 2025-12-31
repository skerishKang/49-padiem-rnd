"""
ONNX 내보내기 자리표시자.
- 실제 모델 export 로직이 없으며, TensorRT 변환 파이프라인에 연결하기 위한 형태만 제공합니다.
- 필요 시: 모델 로드 + torch.onnx.export 등의 실제 내보내기 코드로 교체하세요.
"""

from __future__ import annotations

import argparse
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="ONNX export stub (no-op).")
    parser.add_argument("--output", required=True, help="저장할 ONNX 경로")
    args = parser.parse_args()

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    # 실제 export 대신 빈 파일 생성
    out.write_bytes(b"")
    print(f"[ONNX Stub] created empty ONNX placeholder: {out}")


if __name__ == "__main__":
    main()
