#!/usr/bin/env python3

"""
StormSense RAG Index Builder.

Ingests cyclone observation metadata and IMD guidelines, constructs chunks,
generates embeddings, and outputs a FAISS index with document metadata.
"""

from pathlib import Path
import numpy as np
import pandas as pd

CLEAN_DATA_PATH = Path("stormsense_dataset/processed/clean_observations_v2.csv")
EMBEDDINGS_PATH = Path("stormsense_dataset/features/X_clean.npy")
MAPPING_PATH = Path("stormsense_dataset/features/embedding_mapping.csv")
OUTPUT_INDEX_PATH = Path("stormsense_dataset/features/rag.index")
OUTPUT_META_PATH = Path("stormsense_dataset/features/rag_metadata.json")


def build_rag_index():
    print("=" * 70)
    print("BUILDING STORMSENSE FAISS RAG INDEX")
    print("=" * 70)

    if not CLEAN_DATA_PATH.exists():
        print(f"[ERROR] Clean data file missing: {CLEAN_DATA_PATH}")
        return

    obs_df = pd.read_csv(CLEAN_DATA_PATH)
    print(f"[INFO] Loaded {len(obs_df)} clean observation records.")

    # Load FAISS if available
    try:
        import faiss
        has_faiss = True
    except ImportError:
        has_faiss = False
        print("[WARN] FAISS library not installed. Generating metadata index only.")

    embeddings = None
    if EMBEDDINGS_PATH.exists():
        embeddings = np.load(EMBEDDINGS_PATH).astype(np.float32)
        print(f"[INFO] Loaded vision embeddings: {embeddings.shape}")
    else:
        print(f"[WARN] Embeddings array {EMBEDDINGS_PATH} not found. Generating dummy features.")
        embeddings = np.zeros((len(obs_df), 768), dtype=np.float32)

    if has_faiss:
        dimension = embeddings.shape[1]
        index = faiss.IndexFlatIP(dimension)
        # Normalize vectors for Cosine Similarity
        faiss.normalize_L2(embeddings)
        index.add(embeddings)
        OUTPUT_INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
        faiss.write_index(index, str(OUTPUT_INDEX_PATH))
        print(f"[SUCCESS] Wrote FAISS index ({index.ntotal} vectors) to {OUTPUT_INDEX_PATH}")

    # Build chunk metadata
    metadata = []
    for idx, row in obs_df.iterrows():
        metadata.append({
            "id": idx,
            "storm_id": str(row.get("storm_id")),
            "storm_name": str(row.get("storm_name")),
            "timestamp": str(row.get("timestamp")),
            "wind_kts": float(row.get("wind_kts", 0)) if pd.notna(row.get("wind_kts")) else None,
            "pressure_hpa": float(row.get("pressure_hpa", 0)) if pd.notna(row.get("pressure_hpa")) else None,
            "stage": str(row.get("stage", "organizing")),
            "snippet": f"Cyclone {row.get('storm_name')} ({row.get('storm_id')}) at {row.get('timestamp')}: Wind {row.get('wind_kts')} kts, Pressure {row.get('pressure_hpa')} hPa."
        })

    import json
    OUTPUT_META_PATH.write_text(json.dumps(metadata, indent=2))
    print(f"[SUCCESS] Saved metadata store to {OUTPUT_META_PATH}")


if __name__ == "__main__":
    build_rag_index()
