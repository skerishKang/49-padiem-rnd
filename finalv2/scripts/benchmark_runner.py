import argparse
import csv
import sys
import time
from pathlib import Path
from typing import Any

import psutil


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="성능 측정(지연/메모리/throughput) 실행")
    parser.add_argument("input_dir", help="벤치마크 입력 오디오(.wav) 폴더")
    parser.add_argument("output_csv", help="결과 CSV 경로")
    parser.add_argument(
        "--pipeline-type",
        choices=["quick", "audio", "video"],
        default="quick",
        help="실행 파이프라인 종류(기본: quick)",
    )
    parser.add_argument(
        "--run-root",
        default="",
        help="pipeline_runner의 run_root(미지정 시 finalv2/data/runs/benchmarks 사용)",
    )
    parser.add_argument(
        "--poll-interval",
        type=float,
        default=0.2,
        help="메모리/GPU 사용량 폴링 간격(초)",
    )
    parser.add_argument(
        "--max-files",
        type=int,
        default=0,
        help="최대 실행 파일 수(0이면 전체)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="실제 파이프라인 실행 없이 파일 목록만 CSV로 기록",
    )
    return parser.parse_args()


def find_pipeline_runner(repo_root: Path, finalv2_root: Path) -> Path:
    candidates = [
        repo_root / "orchestrator" / "pipeline_runner.py",
        finalv2_root / "orchestrator" / "pipeline_runner.py",
    ]
    for p in candidates:
        if p.exists():
            return p
    raise FileNotFoundError("pipeline_runner.py를 찾을 수 없습니다.")


def safe_float(value: float) -> float:
    if value is None:
        return 0.0
    return float(value)


def collect_tree_rss_mb(proc: psutil.Process) -> float:
    rss_bytes = 0
    procs = [proc]
    try:
        procs.extend(proc.children(recursive=True))
    except psutil.Error:
        pass

    for p in procs:
        try:
            rss_bytes += p.memory_info().rss
        except psutil.Error:
            continue

    return rss_bytes / (1024 * 1024)


def has_nvidia_smi() -> bool:
    from shutil import which

    return which("nvidia-smi") is not None


def get_gpu_memory_used_mb() -> int | None:
    if not has_nvidia_smi():
        return None

    import subprocess

    try:
        out = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
            text=True,
            stderr=subprocess.DEVNULL,
        )
        values = []
        for line in out.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                values.append(int(line))
            except ValueError:
                continue
        return int(sum(values)) if values else None
    except Exception:
        return None


def iter_audio_files(input_dir: Path) -> list[Path]:
    files = sorted([p for p in input_dir.glob("**/*.wav") if p.is_file()])
    return files


def estimate_wav_duration_sec(path: Path) -> float | None:
    import wave

    try:
        with wave.open(str(path), "rb") as wf:
            frames = wf.getnframes()
            rate = wf.getframerate()
            if rate <= 0:
                return None
            return frames / rate
    except Exception:
        return None


def run_pipeline_and_measure(
    command: list[str],
    cwd: Path,
    poll_interval: float,
) -> dict[str, Any]:
    import subprocess

    start_gpu = get_gpu_memory_used_mb()

    start = time.perf_counter()
    p = subprocess.Popen(command, cwd=str(cwd))

    ps_proc = psutil.Process(p.pid)

    peak_rss_mb = 0.0
    peak_gpu_mb = start_gpu if start_gpu is not None else None

    while True:
        if p.poll() is not None:
            break

        try:
            rss_mb = collect_tree_rss_mb(ps_proc)
            peak_rss_mb = max(peak_rss_mb, rss_mb)
        except psutil.Error:
            pass

        cur_gpu = get_gpu_memory_used_mb()
        if cur_gpu is not None:
            peak_gpu_mb = cur_gpu if peak_gpu_mb is None else max(peak_gpu_mb, cur_gpu)

        time.sleep(poll_interval)

    end = time.perf_counter()

    end_gpu = get_gpu_memory_used_mb()

    elapsed_sec = end - start
    return_code = p.returncode

    gpu_delta_peak_mb = None
    gpu_delta_end_mb = None
    if start_gpu is not None and peak_gpu_mb is not None:
        gpu_delta_peak_mb = max(0, peak_gpu_mb - start_gpu)
    if start_gpu is not None and end_gpu is not None:
        gpu_delta_end_mb = max(0, end_gpu - start_gpu)

    return {
        "elapsed_sec": elapsed_sec,
        "return_code": return_code,
        "cpu_rss_peak_mb": round(peak_rss_mb, 2),
        "gpu_mem_peak_mb": gpu_delta_peak_mb,
        "gpu_mem_end_mb": gpu_delta_end_mb,
    }


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def write_rows(output_csv: Path, rows: list[dict[str, Any]]) -> None:
    ensure_parent(output_csv)

    if not rows:
        output_csv.write_text("", encoding="utf-8")
        return

    fieldnames = list(rows[0].keys())
    with output_csv.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)


def main() -> None:
    args = parse_args()

    script_path = Path(__file__).resolve()
    finalv2_root = script_path.parents[1]
    repo_root = script_path.parents[2]

    input_dir = Path(args.input_dir)
    output_csv = Path(args.output_csv)

    pipeline_runner = find_pipeline_runner(repo_root=repo_root, finalv2_root=finalv2_root)

    if args.run_root:
        run_root = Path(args.run_root)
    else:
        run_root = finalv2_root / "data" / "runs" / "benchmarks"

    files = iter_audio_files(input_dir)
    if args.max_files and args.max_files > 0:
        files = files[: args.max_files]

    rows: list[dict[str, Any]] = []

    for idx, wav_path in enumerate(files):
        clip_id = wav_path.stem
        duration_sec = estimate_wav_duration_sec(wav_path)

        row: dict[str, Any] = {
            "index": idx,
            "id": clip_id,
            "path": str(wav_path),
            "duration_sec": round(duration_sec, 3) if duration_sec is not None else "",
            "pipeline_type": args.pipeline_type,
        }

        if args.dry_run:
            row.update(
                {
                    "elapsed_sec": "",
                    "throughput_clips_per_sec": "",
                    "rtf": "",
                    "cpu_rss_peak_mb": "",
                    "gpu_mem_peak_mb": "",
                    "gpu_mem_end_mb": "",
                    "return_code": "",
                }
            )
            rows.append(row)
            continue

        command = [
            sys.executable,
            str(pipeline_runner),
            "--pipeline-type",
            args.pipeline_type,
            "--input-media",
            str(wav_path),
            "--run-root",
            str(run_root),
        ]

        stats = run_pipeline_and_measure(command=command, cwd=repo_root, poll_interval=args.poll_interval)

        elapsed_sec = safe_float(stats.get("elapsed_sec", 0.0))
        throughput = (1.0 / elapsed_sec) if elapsed_sec > 0 else 0.0
        rtf = (elapsed_sec / duration_sec) if duration_sec and duration_sec > 0 else ""

        row.update(
            {
                "elapsed_sec": round(elapsed_sec, 3),
                "throughput_clips_per_sec": round(throughput, 4),
                "rtf": round(rtf, 4) if isinstance(rtf, float) else "",
                "cpu_rss_peak_mb": stats.get("cpu_rss_peak_mb", ""),
                "gpu_mem_peak_mb": stats.get("gpu_mem_peak_mb", ""),
                "gpu_mem_end_mb": stats.get("gpu_mem_end_mb", ""),
                "return_code": stats.get("return_code", ""),
            }
        )

        rows.append(row)

    write_rows(output_csv, rows)


if __name__ == "__main__":
    main()
