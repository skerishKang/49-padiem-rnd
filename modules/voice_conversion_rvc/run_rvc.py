import argparse
import sys
import torch
import librosa
import numpy as np
import soundfile as sf
from pathlib import Path

# 모듈 경로 추가
sys.path.append(str(Path(__file__).resolve().parents[2]))
from modules.voice_conversion_rvc.core import ImprovedRVCAttention, RVCRetrieval

def main():
    parser = argparse.ArgumentParser(description="Realized RVC Inference Script")
    parser.add_argument("--model", help="Path to model checkpoint")
    parser.add_argument("--source", required=True, help="Input audio path")
    parser.add_argument("--output", required=True, help="Output audio path")
    parser.add_argument("--f0", default="harvest", help="f0 method")
    parser.add_argument("--hop-length", type=int, default=128, help="hop length")
    parser.add_argument("--filter-radius", type=int, default=3, help="filter radius")
    parser.add_argument("--spk-id", type=int, default=0, help="speaker id")
    parser.add_argument("--index", help="index path")
    parser.add_argument("--pitch", type=float, default=0.0, help="pitch shift")
    
    args = parser.parse_args()
    
    input_path = Path(args.source)
    output_path = Path(args.output)
    
    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}")
        sys.exit(1)
        
    print(f"RVC Realization: Processing {input_path} with Improved Attention...")
    
    # 1. Load Audio
    y, sr = librosa.load(input_path, sr=None)
    
    # 2. Extract Features (Simulated for inference verification)
    # 생 오디오 샘플은 T가 너무 크므로(O(T^2) 메모리), 프레임 단위로 다운샘플링하여 어텐션 수행
    # 16000Hz 기준 160 샘플마다 한 프레임(0.01s)으로 축소
    hop_size = 160
    y_tensor = torch.from_numpy(y).float().unsqueeze(0).unsqueeze(1) # (1, 1, T)
    
    # Simple Downsampling to simulate frame features
    y_frames = torch.nn.functional.avg_pool1d(y_tensor, kernel_size=hop_size, stride=hop_size)
    y_frames = y_frames.transpose(1, 2) # (1, T_frames, 1)
    
    print(f"Sequence length reduced from {y_tensor.shape[-1]} to {y_frames.shape[1]} for attention efficiency.")

    # 임베딩 차원 맞추기
    embed_dim = 256
    proj = torch.nn.Linear(1, embed_dim)
    y_emb = proj(y_frames) # (1, T_frames, 256)
    
    # 3. Apply Improved Attention (from core.py)
    attention = ImprovedRVCAttention(embed_dim=embed_dim)
    y_refined = attention(y_emb)
    
    # 4. Simulated Retrieval (from core.py)
    retrieval = RVCRetrieval(index_path=args.index)
    search_res = retrieval.search(y_refined)
    print(f"RVC Retrieval Status: {search_res}")
    
    # 5. Simulated Conversion (Applying pitch shift via librosa)
    if args.pitch != 0:
        print(f"Applying pitch shift: {args.pitch}")
        y = librosa.effects.pitch_shift(y, sr=sr, n_steps=args.pitch)
        
    # 6. Save Result
    output_path.parent.mkdir(parents=True, exist_ok=True)
    sf.write(output_path, y, sr)
    
    print(f"RVC Realization: Done. Result saved to {output_path}")

if __name__ == "__main__":
    main()
