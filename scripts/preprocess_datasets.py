"""
데이터셋 전처리 스크립트
- 샘플레이트 통일 (22kHz)
- 모노 채널 변환
- 각 데이터셋별 처리
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import subprocess
import sys
import shutil
from pathlib import Path
from typing import Optional
from tqdm import tqdm

# 목표 샘플레이트 (22kHz - TTS 표준)
TARGET_SAMPLE_RATE = 22050

# 데이터셋 경로 설정
DATASETS_DIR = Path(__file__).parent.parent / "datasets"


def get_ffmpeg_path() -> str:
    """ffmpeg 경로 반환"""
    return "ffmpeg"


def resample_audio(input_path: Path, output_path: Path, sample_rate: int = TARGET_SAMPLE_RATE) -> bool:
    """
    오디오 파일 리샘플링
    - 모노 채널로 변환
    - 지정된 샘플레이트로 변환
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    command = [
        get_ffmpeg_path(),
        "-y",  # 덮어쓰기
        "-i", str(input_path),
        "-ar", str(sample_rate),
        "-ac", "1",  # 모노
        "-acodec", "pcm_s16le",  # 16-bit PCM
        str(output_path),
    ]
    
    try:
        subprocess.run(command, check=True, capture_output=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error resampling {input_path}: {e.stderr.decode() if e.stderr else 'unknown'}")
        return False


def process_kss(datasets_dir: Path) -> dict:
    """
    KSS 데이터셋 전처리
    - 원본: 44.1kHz
    - 구조: datasets/kss/kss/1~4/*.wav + transcript.v.1.4.txt
    """
    kss_dir = datasets_dir / "kss"
    output_dir = datasets_dir / "kss_processed"
    output_dir.mkdir(exist_ok=True)
    
    stats = {"processed": 0, "failed": 0, "skipped": 0}
    
    # transcript 파싱
    transcript_path = kss_dir / "transcript.v.1.4.txt"
    if not transcript_path.exists():
        transcript_path = kss_dir / "kss" / "transcript.v.1.4.txt"
    
    transcripts = {}
    if transcript_path.exists():
        with open(transcript_path, "r", encoding="utf-8") as f:
            for line in f:
                parts = line.strip().split("|")
                if len(parts) >= 2:
                    full_filename = parts[0].strip()
                    filename_only = Path(full_filename).name.replace(".wav", "")
                    text = parts[1].strip() if len(parts) > 1 else ""
                    transcripts[filename_only] = text
    
    # WAV 파일 처리
    wav_dirs = [kss_dir / "kss" / str(i) for i in range(1, 5)]
    if not any(d.exists() for d in wav_dirs):
        wav_dirs = [kss_dir / str(i) for i in range(1, 5)]
    
    metadata = []
    
    for wav_dir in wav_dirs:
        if not wav_dir.exists():
            continue
        
        for wav_file in tqdm(sorted(wav_dir.glob("*.wav")), desc=f"[KSS] {wav_dir.name}"):
            rel_name = wav_file.name.replace(".wav", "")
            output_path = output_dir / "wavs" / wav_file.name
            
            text = transcripts.get(rel_name, "")
            
            if output_path.exists():
                stats["skipped"] += 1
                if text:
                    metadata.append({"id": rel_name, "audio": f"wavs/{wav_file.name}", "text": text})
                continue
            
            if resample_audio(wav_file, output_path):
                stats["processed"] += 1
                if text:
                    metadata.append({"id": rel_name, "audio": f"wavs/{wav_file.name}", "text": text})
            else:
                stats["failed"] += 1
    
    # 메타데이터 저장
    if metadata:
        with open(output_dir / "metadata.json", "w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
            
        with open(output_dir / "metadata.csv", "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f, delimiter="|")
            for item in metadata:
                writer.writerow([item["id"], item["text"]])
    
    print(f"[KSS] Processed: {stats['processed']}, Skipped: {stats['skipped']}, Failed: {stats['failed']}")
    return stats


def process_ravdess(datasets_dir: Path) -> dict:
    ravdess_dir = datasets_dir / "ravdess"
    output_dir = datasets_dir / "ravdess_processed"
    output_dir.mkdir(exist_ok=True)
    
    stats = {"processed": 0, "failed": 0, "skipped": 0}
    emotion_map = {"01":"neutral","02":"calm","03":"happy","04":"sad","05":"angry","06":"fearful","07":"disgust","08":"surprised"}
    metadata = []
    
    for actor_dir in sorted(ravdess_dir.glob("Actor_*")):
        actor_id = actor_dir.name
        for wav_file in sorted(actor_dir.glob("*.wav")):
            output_name = f"{actor_id}_{wav_file.name}"
            output_path = output_dir / "wavs" / output_name
            
            parts = wav_file.stem.split("-")
            emotion = emotion_map.get(parts[2], "unknown") if len(parts) >= 3 else "unknown"
            entry = {"id": f"{actor_id}_{wav_file.stem}", "audio": f"wavs/{output_name}", "emotion": emotion, "actor": actor_id}
            
            if output_path.exists():
                stats["skipped"] += 1
                metadata.append(entry)
                continue
            
            if resample_audio(wav_file, output_path):
                stats["processed"] += 1
                metadata.append(entry)
            else:
                stats["failed"] += 1
    
    if metadata:
        with open(output_dir / "metadata.json", "w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
    return stats


def process_vctk(datasets_dir: Path) -> dict:
    vctk_dir = datasets_dir / "vctk" / "VCTK-Corpus" / "VCTK-Corpus"
    output_dir = datasets_dir / "vctk_processed"
    output_dir.mkdir(exist_ok=True)
    
    stats = {"processed": 0, "failed": 0, "skipped": 0}
    wav_dir = vctk_dir / "wav48"
    txt_dir = vctk_dir / "txt"
    
    if not wav_dir.exists(): return stats
    
    metadata = []
    for speaker_dir in tqdm(sorted(wav_dir.glob("p*")), desc="[VCTK]"):
        speaker_id = speaker_dir.name
        for wav_file in sorted(speaker_dir.glob("*.wav")):
            output_path = output_dir / "wavs" / speaker_id / wav_file.name
            
            txt_file = txt_dir / speaker_id / f"{wav_file.stem}.txt"
            text = txt_file.read_text(encoding="utf-8").strip() if txt_file.exists() else ""
            entry = {"id": f"{speaker_id}_{wav_file.stem}", "audio": f"wavs/{speaker_id}/{wav_file.name}", "text": text, "speaker": speaker_id}
            
            if output_path.exists():
                stats["skipped"] += 1
                metadata.append(entry)
                continue
            
            if resample_audio(wav_file, output_path):
                stats["processed"] += 1
                metadata.append(entry)
            else:
                stats["failed"] += 1
                
    if metadata:
        with open(output_dir / "metadata.json", "w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
    return stats


def process_ljspeech(datasets_dir: Path) -> dict:
    lj_dir = datasets_dir / "ljspeech" / "LJSpeech-1.1"
    if not lj_dir.exists(): lj_dir = datasets_dir / "ljspeech"
    
    output_dir = datasets_dir / "ljspeech_processed"
    output_dir.mkdir(exist_ok=True)
    
    stats = {"processed": 0, "failed": 0, "skipped": 0}
    src_metadata = lj_dir / "metadata.csv"
    if src_metadata.exists():
        shutil.copy(src_metadata, output_dir / "metadata.csv")
    
    wav_dir = lj_dir / "wavs"
    output_wav_dir = output_dir / "wavs"
    output_wav_dir.mkdir(exist_ok=True)
    
    metadata = []
    if src_metadata.exists():
        with open(src_metadata, "r", encoding="utf-8") as f:
            for line in f:
                parts = line.strip().split("|")
                if len(parts) >= 2:
                    file_id, text = parts[0], parts[1]
                    norm_text = parts[2] if len(parts) > 2 else text
                    src_wav, dst_wav = wav_dir / f"{file_id}.wav", output_wav_dir / f"{file_id}.wav"
                    
                    entry = {"id": file_id, "audio": f"wavs/{file_id}.wav", "text": text, "text_normalized": norm_text}
                    
                    if dst_wav.exists():
                        stats["skipped"] += 1
                    elif src_wav.exists():
                        if resample_audio(src_wav, dst_wav): stats["processed"] += 1
                        else: stats["failed"] += 1
                    metadata.append(entry)
                    
    if metadata:
        with open(output_dir / "metadata.json", "w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
    return stats


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", choices=["all", "kss", "ravdess", "vctk", "ljspeech"], default="all")
    parser.add_argument("--datasets-dir", type=Path, default=DATASETS_DIR)
    args = parser.parse_args()
    
    total_stats = {"processed": 0, "failed": 0, "skipped": 0}
    if args.dataset in ["all", "kss"]:
        s = process_kss(args.datasets_dir)
        for k in total_stats: total_stats[k] += s.get(k, 0)
    if args.dataset in ["all", "ravdess"]:
        s = process_ravdess(args.datasets_dir)
        for k in total_stats: total_stats[k] += s.get(k, 0)
    if args.dataset in ["all", "vctk"]:
        s = process_vctk(args.datasets_dir)
        for k in total_stats: total_stats[k] += s.get(k, 0)
    if args.dataset in ["all", "ljspeech"]:
        s = process_ljspeech(args.datasets_dir)
        for k in total_stats: total_stats[k] += s.get(k, 0)
    
    print(f"\nTotal -> Processed: {total_stats['processed']}, Skipped: {total_stats['skipped']}, Failed: {total_stats['failed']}")

if __name__ == "__main__":
    main()
