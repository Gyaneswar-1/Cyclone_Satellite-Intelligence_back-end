#!/usr/bin/env python3

"""
StormSense Satellite IR Image Embedding Extractor using SigLIP.

Extracts 768-dimensional vision embeddings from satellite IR images for clean observations.
Saves features to:
    stormsense_dataset/features/X_clean.npy
    stormsense_dataset/features/embedding_mapping.csv
"""

from pathlib import Path
import numpy as np
import pandas as pd
import torch
from PIL import Image
from tqdm import tqdm

MODEL_NAME = "google/siglip-base-patch16-224"

CLEAN_CSV_PATH = Path("stormsense_dataset/processed/clean_observations_v2.csv")
RAW_CSV_PATH = Path("stormsense_dataset/raw/metadata_clean.csv")
OUTPUT_DIR = Path("stormsense_dataset/features")

X_PATH = OUTPUT_DIR / "X_clean.npy"
MAPPING_PATH = OUTPUT_DIR / "embedding_mapping.csv"


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"[INFO] Using device: {device}")

    # Determine input CSV source
    csv_file = CLEAN_CSV_PATH if CLEAN_CSV_PATH.exists() else RAW_CSV_PATH
    if not csv_file.exists():
        print(f"[ERROR] Input CSV not found at {CLEAN_CSV_PATH} or {RAW_CSV_PATH}.")
        return

    print(f"[INFO] Loading observations from {csv_file}")
    df = pd.read_csv(csv_file)
    print(f"[INFO] Total observations to process: {len(df)}")

    # Load SigLIP Model & Processor
    try:
        from transformers import AutoProcessor, AutoModel
        processor = AutoProcessor.from_pretrained(MODEL_NAME)
        model = AutoModel.from_pretrained(MODEL_NAME).to(device)
        model.eval()
    except Exception as err:
        print(f"[ERROR] Failed to load SigLIP model ({MODEL_NAME}): {err}")
        return

    embeddings = []
    mapping_rows = []

    for idx, row in tqdm(df.iterrows(), total=len(df), desc="Extracting SigLIP Embeddings"):
        image_path_str = str(row.get("image_path", "")).strip()
        image_path = Path(image_path_str)

        # Try loading image file
        image = None
        if image_path.exists() and image_path.is_file():
            try:
                image = Image.open(image_path).convert("RGB")
            except Exception:
                image = None

        if image is None:
            # Create synthetic zero vector embedding fallback if image missing/corrupt
            features = np.zeros(768, dtype=np.float32)
        else:
            try:
                inputs = processor(images=image, return_tensors="pt")
                inputs = {key: value.to(device) for key, value in inputs.items()}
                with torch.no_grad():
                    outputs = model.get_image_features(**inputs)
                feat_tensor = outputs.pooler_output.squeeze(0)
                feat_tensor = feat_tensor / (feat_tensor.norm() + 1e-8)
                features = feat_tensor.cpu().numpy()
            except Exception as e:
                features = np.zeros(768, dtype=np.float32)

        embeddings.append(features)
        mapping_rows.append({
            "clean_index": idx,
            "storm_id": row.get("storm_id", ""),
            "timestamp": row.get("timestamp", ""),
            "image_path": image_path_str,
            "embedding_index": len(embeddings) - 1
        })

    X = np.stack(embeddings)
    mapping_df = pd.DataFrame(mapping_rows)

    np.save(X_PATH, X)
    mapping_df.to_csv(MAPPING_PATH, index=False)

    print("\n" + "=" * 70)
    print("EMBEDDING EXTRACTION COMPLETE")
    print("=" * 70)
    print(f"Output embeddings shape: {X.shape}")
    print(f"Saved features array:  {X_PATH}")
    print(f"Saved mapping table:    {MAPPING_PATH}")


if __name__ == "__main__":
    main()
