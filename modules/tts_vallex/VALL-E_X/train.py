import argparse
import logging
import os
from pathlib import Path

import torch
import torch.distributed as dist
from torch.nn.parallel import DistributedDataParallel as DDP
from torch.utils.data import DataLoader

from models.vallex import VALLE
from data.datamodule import TtsDataModule
from lhotse import CutSet

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
LOGGER = logging.getLogger("train_vallex")

def setup_ddp():
    if "RANK" in os.environ:
        dist.init_process_group(backend="nccl")
        rank = int(os.environ["RANK"])
        world_size = int(os.environ["WORLD_SIZE"])
        gpu = int(os.environ["LOCAL_RANK"])
        torch.cuda.set_device(gpu)
        LOGGER.info(f"DDP Initialized: Rank {rank}, World Size {world_size}, GPU {gpu}")
        return rank, world_size, gpu
    else:
        LOGGER.info("DDP not used. Running on single device.")
        return 0, 1, 0

def train(args):
    rank, world_size, gpu = setup_ddp()
    device = torch.device(f"cuda:{gpu}" if torch.cuda.is_available() else "cpu")
    # device = torch.device("cpu")

    # Load Model
    # Note: These parameters should match your config or checkpoint
    model = VALLE(
        d_model=1024,
        nhead=16,
        num_layers=12,
        num_quantizers=8
    ).to(device)

    if world_size > 1:
        model = DDP(model, device_ids=[gpu])

    # Load Data (Lhotse)
    cuts_train = CutSet.from_file(args.cuts_train)
    LOGGER.info(f"Loaded {len(cuts_train)} cuts for training.")

    # Data Loading
    datamodule = TtsDataModule(args)
    # Note: Using the validated cuts
    train_dl = datamodule.train_dataloaders(cuts_train)

    # Optimizer
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr)

    model.train()
    for epoch in range(args.epochs):
        LOGGER.info(f"Starting Epoch {epoch}")
        for batch_idx, batch in enumerate(train_dl):
            # Prepare inputs
            # TtsDataModule/AudioDataset usually returns a dict with these keys
            text_tokens = batch['text_tokens'].to(device)
            text_tokens_lens = batch['text_tokens_lens'].to(device)
            audio_features = batch['audio_features'].to(device) # (B, Q, T)
            audio_features_lens = batch['audio_features_lens'].to(device)
            
            # Map languages/emotions if available
            # For now, we assume emotions are passed or default to neutral
            # You might need to add emotion_ids to your dataset/collate
            emotion_ids = torch.zeros(text_tokens.shape[0], dtype=torch.long).to(device) # Default neutral

            # Forward
            # stage 1 (AR) expects audio_features as (B, T, Q) or handled inside ar_decoder
            # Stage 1: Predict first quantizer
            # Stage 2: Predict higher quantizers
            loss, metrics = model(
                text_tokens, text_tokens_lens, 
                audio_features, audio_features_lens, 
                train_stage=args.stage,
                emotion_ids=emotion_ids
            )

            # Optimization
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            if batch_idx % 10 == 0:
                LOGGER.info(f"Epoch {epoch}, Batch {batch_idx}, Loss: {loss.item():.4f}")
            
            if batch_idx >= args.max_batches: # For demo/test
                break

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--cuts-train", required=True, help="Path to cuts_train.jsonl.gz")
    parser.add_argument("--epochs", type=int, default=1)
    parser.add_argument("--lr", type=float, default=1e-4)
    parser.add_argument("--stage", type=int, default=1, help="1 for AR, 2 for NAR")
    parser.add_argument("--max-batches", type=int, default=5, help="Stop after N batches for verification")
    
    # Add TtsDataModule specific arguments
    TtsDataModule.add_arguments(parser)
    
    args = parser.parse_args()
    train(args)
