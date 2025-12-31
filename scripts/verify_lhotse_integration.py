import os
import json
import gzip
from pathlib import Path
from lhotse import Recording, SupervisionSegment, RecordingSet, SupervisionSet, CutSet

def validate_ljspeech_lhotse():
    print("Starting Lhotse manifest generation for LJSpeech...")
    
    # Paths
    base_dir = Path("G:/Ddrive/BatangD/task/workdiary/49-padiem-rnd")
    audio_dir = base_dir / "datasets/ljspeech_processed/wavs"
    output_dir = base_dir / "modules/tts_vallex/VALL-E_X/data/tokenized"
    os.makedirs(output_dir, exist_ok=True)
    
    # Load consolidated manifest to get LJSpeech entries
    consolidated_path = base_dir / "datasets/train_manifest.jsonl"
    if not consolidated_path.exists():
        print(f"Error: Consolidated manifest not found at {consolidated_path}")
        return

    recordings = []
    supervisions = []
    
    count = 0
    with open(consolidated_path, "r", encoding="utf-8") as f:
        for line in f:
            item = json.loads(line)
            # LJSpeech IDs start with 'lj_' as per consolidate_metadata.py
            if item["id"].startswith("lj_"):
                # audio_path in manifest is relative to 'datasets' directory
                # e.g., "ljspeech_processed/wavs/LJ001-0001.wav"
                audio_rel_path = item["audio_path"]
                audio_path = base_dir / "datasets" / audio_rel_path
                
                if not audio_path.exists():
                    print(f"Warning: Audio not found: {audio_path}")
                    continue
                
                # Create Lhotse Recording
                recording = Recording.from_file(audio_path, recording_id=item["id"])
                
                # Create Lhotse Supervision
                supervision = SupervisionSegment(
                    id=item["id"],
                    recording_id=item["id"],
                    start=0.0,
                    duration=recording.duration,
                    text=item["text"],
                    language=item["language"],
                    speaker=item["speaker"],
                    custom={"normalized_text": item["text"]}
                )
                
                recordings.append(recording)
                supervisions.append(supervision)
                count += 1
                if count >= 100: # Test with first 100 samples
                    break
    
    if not recordings:
        print("Error: No LJSpeech recordings found matching the criteria.")
        return

    recording_set = RecordingSet.from_items(recordings)
    supervision_set = SupervisionSet.from_items(supervisions)
    cut_set = CutSet.from_manifests(recordings=recording_set, supervisions=supervision_set)
    
    # Save as .jsonl.gz for VALL-E X DataModule compatibility
    cut_set.to_file(output_dir / "cuts_train.jsonl.gz")
    print(f"Successfully generated Lhotse manifest with {len(cut_set)} cuts.")
    print(f"Manifest saved to: {output_dir / 'cuts_train.jsonl.gz'}")

if __name__ == "__main__":
    validate_ljspeech_lhotse()
