import argparse
import os
import sys
import subprocess
import yaml
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description="MuseTalk LipSync Wrapper")
    parser.add_argument("--input_video", required=True, help="Path to input video")
    parser.add_argument("--input_audio", required=True, help="Path to input audio")
    parser.add_argument("--output_video", required=True, help="Path to output video")
    parser.add_argument("--config", default="modules/lipsync_musetalk/config/settings.yaml", help="Path to base config")
    args = parser.parse_args()

    # MuseTalk 설치 경로 (예상)
    musetalk_root = Path(__file__).parent / "MuseTalk"
    
    if not musetalk_root.exists():
        print(f"[Error] MuseTalk directory not found at {musetalk_root}")
        print("Please clone MuseTalk repository: git clone https://github.com/TMElyralab/MuseTalk.git modules/lipsync_musetalk/MuseTalk")
        print("And install dependencies.")
        # 임시로 실패 처리하지 않고 더미 파일 생성 (테스트용) - 실제 배포시는 제거
        # shutil.copy(args.input_video, args.output_video)
        sys.exit(1)

    # 임시 추론 설정 파일 생성
    inference_config = {
        "task_0": {
            "video_path": args.input_video,
            "audio_path": args.input_audio,
            "bbox_shift": 0,
            "video_out_path": args.output_video,
            "fp16": True
        }
    }
    
    temp_config_path = musetalk_root / "configs" / "inference" / "temp_inference.yaml"
    temp_config_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(temp_config_path, "w", encoding="utf-8") as f:
        yaml.dump(inference_config, f)

    # MuseTalk 추론 실행
    # python -m scripts.inference --inference_config ...
    cmd = [
        sys.executable, "-m", "scripts.inference",
        "--inference_config", str(temp_config_path)
    ]
    
    print(f"Running MuseTalk: {' '.join(cmd)}")
    
    # MuseTalk 루트에서 실행해야 경로 문제 없음
    env = os.environ.copy()
    env["PYTHONPATH"] = str(musetalk_root) + os.pathsep + env.get("PYTHONPATH", "")
    
    try:
        subprocess.run(cmd, cwd=musetalk_root, env=env, check=True)
        print(f"MuseTalk inference completed: {args.output_video}")
    except subprocess.CalledProcessError as e:
        print(f"MuseTalk execution failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
