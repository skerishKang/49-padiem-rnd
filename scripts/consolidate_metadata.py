"""
VALL-E X 학습용 통합 메타데이터 생성 스크립트
- 전처리된 각 데이터셋의 metadata.json을 읽어 하나의 JSONL 파일로 통합
- VALL-E X 학습 포맷(id, audio_path, text, language, speaker, emotion) 구성
"""

import json
from pathlib import Path

# 설정
DATASETS_DIR = Path("G:/Ddrive/BatangD/task/workdiary/49-padiem-rnd/datasets")
OUTPUT_FILE = DATASETS_DIR / "train_manifest.jsonl"

def consolidate_metadata():
    all_entries = []
    
    # KSS (한국어)
    kss_meta = DATASETS_DIR / "kss_processed" / "metadata.json"
    print(f"Checking KSS meta: {kss_meta}")
    if kss_meta.exists():
        with open(kss_meta, "r", encoding="utf-8") as f:
            data = json.load(f)
            for entry in data:
                all_entries.append({
                    "id": f"kss_{entry['id']}",
                    "audio_path": str(Path("kss_processed") / entry["audio"]),
                    "text": entry["text"],
                    "language": "ko",
                    "speaker": "kss_female",
                    "emotion": "neutral"
                })
        print(f"KSS entries added: {len(data)}")
    else:
        print("KSS meta not found")

    # RAVDESS (영어/감정)
    rav_meta = DATASETS_DIR / "ravdess_processed" / "metadata.json"
    print(f"Checking RAVDESS meta: {rav_meta}")
    if rav_meta.exists():
        with open(rav_meta, "r", encoding="utf-8") as f:
            data = json.load(f)
            for entry in data:
                all_entries.append({
                    "id": entry["id"],
                    "audio_path": str(Path("ravdess_processed") / entry["audio"]),
                    "text": "", # RAVDESS는 텍스트 미제공 (보통 고정 문장)
                    "language": "en",
                    "speaker": f"rav_{entry['actor']}",
                    "emotion": entry["emotion"]
                })
        print(f"RAVDESS entries added: {len(data)}")
    else:
        print("RAVDESS meta not found")

    # VCTK (영어/다화자)
    vctk_meta = DATASETS_DIR / "vctk_processed" / "metadata.json"
    print(f"Checking VCTK meta: {vctk_meta}")
    if vctk_meta.exists():
        with open(vctk_meta, "r", encoding="utf-8") as f:
            data = json.load(f)
            for entry in data:
                all_entries.append({
                    "id": f"vctk_{entry['id']}",
                    "audio_path": str(Path("vctk_processed") / entry["audio"]),
                    "text": entry["text"],
                    "language": "en",
                    "speaker": f"vctk_{entry['speaker']}",
                    "emotion": "neutral"
                })
        print(f"VCTK entries added: {len(data)}")
    else:
        print("VCTK meta not found")

    # LJSpeech (영어)
    lj_meta = DATASETS_DIR / "ljspeech_processed" / "metadata.json"
    print(f"Checking LJSpeech meta: {lj_meta}")
    if lj_meta.exists():
        with open(lj_meta, "r", encoding="utf-8") as f:
            data = json.load(f)
            for entry in data:
                all_entries.append({
                    "id": f"lj_{entry['id']}",
                    "audio_path": str(Path("ljspeech_processed") / entry["audio"]),
                    "text": entry["text"],
                    "language": "en",
                    "speaker": "lj_female",
                    "emotion": "neutral"
                })
        print(f"LJSpeech entries added: {len(data)}")
    else:
        print("LJSpeech meta not found")

    # JSONL 저장
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for entry in all_entries:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
            
    print(f"\nTotal entries consolidated to {OUTPUT_FILE}: {len(all_entries)}")

if __name__ == "__main__":
    consolidate_metadata()
