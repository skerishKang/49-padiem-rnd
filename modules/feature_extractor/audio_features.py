from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import librosa
import numpy as np
import soundfile as sf

try:
    import pywt
except ImportError:
    pywt = None

try:
    import torchcrepe
    import torch
except ImportError:
    torchcrepe = None
    torch = None


def load_audio(path: Path, sr: int) -> tuple[np.ndarray, int]:
    y, _ = librosa.load(path, sr=sr, mono=True)
    return y, sr


def extract_mfcc(y: np.ndarray, sr: int, n_mfcc: int = 13) -> list[float]:
    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=n_mfcc)
    return mfcc.mean(axis=1).tolist()


def extract_pitch_yin(y: np.ndarray, sr: int, frame_length: int = 2048, hop_length: int = 512) -> float:
    f0 = librosa.yin(y, fmin=50, fmax=sr // 2, frame_length=frame_length, hop_length=hop_length)
    return float(np.nanmean(f0))


def extract_pitch_crepe(y: np.ndarray, sr: int) -> float:
    """CREPE 기반 고정밀 피치 추출 (torchcrepe 필요)"""
    if torchcrepe is None or torch is None:
        return float("nan")
    
    device = "cuda" if torch.cuda.is_available() else "cpu"
    audio = torch.from_numpy(y).unsqueeze(0).to(device)
    # crepe-tiny 모델 사용 (속도 우선)
    probabilities, values = torchcrepe.predict(
        audio,
        sr,
        hop_length=512,
        fmin=50.0,
        fmax=1000.0,
        model='tiny',
        device=device,
        return_periodicity=True
    )
    # 주기성(periodicity) 기반 필터링
    f0 = torchcrepe.threshold.mean(probabilities, values, threshold=0.1)
    return float(f0.mean().cpu().numpy())


def extract_formants_lpc(y: np.ndarray, sr: int, order: int = 16) -> list[float]:
    # 간단 LPC 기반 포먼트 근사
    a = librosa.lpc(y, order=order)
    roots = np.roots(a)
    roots = [r for r in roots if np.imag(r) >= 0.01]
    angs = np.arctan2(np.imag(roots), np.real(roots))
    freqs = sorted(angs * (sr / (2 * np.pi)))
    return freqs[:4]


def extract_wavelet_energy(y: np.ndarray) -> float:
    if pywt is None:
        return float("nan")
    coeffs = pywt.wavedec(y, "db4", level=3)
    energy = sum(np.sum(c**2) for c in coeffs)
    return float(energy / len(y))


def run(path: Path, sr: int, output: Path) -> None:
    y, sr = load_audio(path, sr)
    feats: dict[str, Any] = {
        "mfcc_mean": extract_mfcc(y, sr),
        "pitch_yin": extract_pitch_yin(y, sr),
        "pitch_crepe": extract_pitch_crepe(y, sr),
        "formants_lpc": extract_formants_lpc(y, sr),
        "wavelet_energy": extract_wavelet_energy(y),
    }
    with open(output, "w", encoding="utf-8") as f:
        json.dump(feats, f, ensure_ascii=False, indent=2)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--sample_rate", type=int, default=16000)
    args = parser.parse_args()

    run(Path(args.input), args.sample_rate, Path(args.output))


if __name__ == "__main__":
    main()
