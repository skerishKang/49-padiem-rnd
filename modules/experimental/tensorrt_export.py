from __future__ import annotations

import argparse
import subprocess
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="TensorRT 변환 실행 스크립트")
    parser.add_argument("--onnx", required=True, help="입력 ONNX 경로")
    parser.add_argument("--engine", required=True, help="저장할 TensorRT 엔진 경로(.plan)")
    parser.add_argument(
        "--trtexec",
        default=r"g:\Ddrive\BatangD\task\workdiary\49-padiem-rnd\TensorRT\TensorRT-10.13.2.6\bin\trtexec.exe",
        help="trtexec 실행 파일 경로",
    )
    parser.add_argument("--fp16", action="store_true", help="FP16 엔진 생성")
    parser.add_argument("--workspace", default="4096", help="workspace 크기(MB)")
    args = parser.parse_args()

    onnx = Path(args.onnx)
    engine = Path(args.engine)
    trtexec = Path(args.trtexec)

    if not onnx.exists():
        print(f"[TensorRT] ONNX 파일이 없습니다: {onnx}")
        return
    if not trtexec.exists():
        print(f"[TensorRT] trtexec를 찾을 수 없습니다: {trtexec}")
        return

    engine.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        str(trtexec),
        f"--onnx={onnx}",
        f"--saveEngine={engine}",
        f"--workspace={args.workspace}",
    ]
    if args.fp16:
        cmd.append("--fp16")

    print("[TensorRT] 실행 명령:", " ".join(cmd))
    try:
        subprocess.run(cmd, check=True)
        print(f"[TensorRT] 엔진 생성 완료: {engine}")
    except subprocess.CalledProcessError as exc:
        print(f"[TensorRT] 변환 실패: {exc}")


if __name__ == "__main__":
    main()
