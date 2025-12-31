import torch
import torchaudio
from lhotse import CutSet, Features, FeatureSet, RecordingSet
from lhotse.serialization import SequentialJsonlWriter
from encodec import EncodecModel
from encodec.utils import convert_audio
from pathlib import Path
import numpy as np
from tqdm import tqdm

def main():
    # Load existing cuts
    cuts_path = "modules/tts_vallex/VALL-E_X/data/tokenized/cuts_train.jsonl.gz"
    output_dir = Path("modules/tts_vallex/VALL-E_X/data/tokenized/features")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    cuts = CutSet.from_file(cuts_path)
    
    # Load EnCodec model
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = EncodecModel.encodec_model_24khz()
    model.set_target_bandwidth(6.0)
    model.to(device)
    
    new_cuts = []
    
    print(f"Extracting EnCodec tokens for {len(cuts)} cuts...")
    for cut in tqdm(cuts):
        # Load audio (keep on CPU for resampling)
        audio = cut.load_audio() # (C, T)
        audio_tensor = torch.from_numpy(audio).float()
        
        # Resample to 24kHz if needed (on CPU)
        if cut.sampling_rate != 24000:
            audio_tensor = convert_audio(audio_tensor, cut.sampling_rate, 24000, 1)
        
        # Move to GPU for EnCodec if available
        audio_tensor = audio_tensor.to(device)
        
        # Add batch dim
        if audio_tensor.ndim == 2:
            audio_tensor = audio_tensor.unsqueeze(0)
            
        # Encode
        with torch.no_grad():
            encoded_frames = model.encode(audio_tensor)
            # codes: (B, Q, T)
            codes = torch.cat([encoded[0] for encoded in encoded_frames], dim=-1)
            codes = codes.squeeze(0).cpu().numpy() # (Q, T)
            codes = codes.T # (T, Q) - Lhotse expects (num_frames, num_features)
            
        # Save as numpy
        feat_path = output_dir / f"{cut.id}.npy"
        np.save(feat_path, codes)
        
        # Create Lhotse Features (Using correct positional arguments/keyword order)
        # 24kHz EnCodec has 75 frames per second
        frame_shift = 1.0 / 75.0 
        
        features = Features(
            type="encodec",
            num_frames=codes.shape[0], # codes is (T, Q)
            num_features=codes.shape[1],
            frame_shift=frame_shift,
            sampling_rate=24000,
            start=0,
            duration=cut.duration,
            storage_type="numpy_files",
            storage_path=str(output_dir), # Directory where numpy files are
            storage_key=feat_path.name,   # Filename
            recording_id=cut.recording.id,
            channels=0
        )
        
        # Attach features to a new cut
        new_cut = cut.copy()
        for sup in new_cut.supervisions:
            if sup.custom is None:
                sup.custom = {}
            sup.custom["normalized_text"] = sup.text
            
        new_cut.features = features
        new_cuts.append(new_cut)
        
    # Save new cuts
    new_cuts = CutSet.from_cuts(new_cuts)
    new_cuts.to_file(cuts_path.replace(".jsonl.gz", "_with_feats.jsonl.gz"))
    print("Done!")

if __name__ == "__main__":
    main()
