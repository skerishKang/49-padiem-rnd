"""
Demucs 보컬 분리 실험용 스텁 모듈.
- 실제 파이프라인에 연결되지 않으며, 연구노트 기록을 재현하기 위한 자리표시자임.
- 추후 통합 시 run_demucs()를 파이프라인에 연결하고, requirements에 demucs를 추가해야 함.
"""

from __future__ import annotations

from pathlib import Path
import subprocess


def run_demucs(input_wav: Path, vocals_out: Path, inst_out: Path) -> None:
    command = [
        "demucs",
        "-n",
        "htdemucs",
        "--two-stems",
        "vocals",
        str(input_wav),
        "--out",
        str(inst_out.parent),
    ]
    # 실제 실행 대신 명령만 기록
    print("Demucs 명령(참고용):", " ".join(command))
    print(f"출력 예상: 보컬={vocals_out}, 반주={inst_out}")
