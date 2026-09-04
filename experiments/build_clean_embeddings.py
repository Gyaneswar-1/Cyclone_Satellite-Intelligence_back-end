import pandas as pd
import numpy as np
from pathlib import Path


# ============================================================
# CONFIGURATION
# ============================================================

ORIGINAL_DATA = "stormsense_dataset/raw/metadata_clean.csv"
CLEAN_DATA = "stormsense_dataset/processed/clean_observations_v2.csv"
EMBEDDINGS = "Training Overhead/v1_features/X.npy"

OUTPUT_EMBEDDINGS = "stormsense_dataset/features/X_clean.npy"
OUTPUT_MAPPING = "stormsense_dataset/features/embedding_mapping.csv"


# ============================================================
# LOAD DATA
# ============================================================

original_df = pd.read_csv(ORIGINAL_DATA)
clean_df = pd.read_csv(CLEAN_DATA)
X = np.load(EMBEDDINGS)


# ============================================================
# BASIC CHECK
# ============================================================

print("=" * 70)
print("BUILDING CLEAN EMBEDDING DATASET")
print("=" * 70)

print("Original rows:", len(original_df))
print("Embedding rows:", len(X))
print("Clean observations:", len(clean_df))
print()


if len(original_df) != len(X):

    raise ValueError(
        "Original dataset rows and embedding rows do not match."
    )


# ============================================================
# NORMALIZE PATH STRINGS
# ============================================================

original_df["image_path"] = (
    original_df["image_path"]
    .astype(str)
    .str.strip()
)

clean_df["image_path"] = (
    clean_df["image_path"]
    .astype(str)
    .str.strip()
)


# ============================================================
# UNIQUE IMAGE PATHS
# ============================================================

unique_images = original_df["image_path"].nunique()

print(
    "Unique image paths in original dataset:",
    unique_images
)

print()


# ============================================================
# BUILD ONE EMBEDDING PER IMAGE PATH
# ============================================================

# IMPORTANT:
# Multiple original rows may point to the same physical image.
#
# We check that those rows have identical embeddings.
#
# The first embedding is retained because identical embeddings
# represent the same image.


image_to_embedding = {}

inconsistent_embeddings = []

duplicate_image_count = 0


for image_path, group in original_df.groupby(
    "image_path",
    sort=False
):

    indices = group.index.to_numpy()

    reference = X[indices[0]]

    # Check all other embeddings belonging to the
    # same image path.
    for idx in indices[1:]:

        if not np.allclose(
            reference,
            X[idx],
            atol=1e-6
        ):

            inconsistent_embeddings.append(
                image_path
            )

            break

    image_to_embedding[image_path] = reference

    if len(indices) > 1:
        duplicate_image_count += 1


# ============================================================
# REPORT EMBEDDING CONSISTENCY
# ============================================================

print("=" * 70)
print("EMBEDDING DUPLICATION CHECK")
print("=" * 70)

print(
    "Images appearing in multiple original rows:",
    duplicate_image_count
)

print(
    "Images with inconsistent embeddings:",
    len(set(inconsistent_embeddings))
)

if inconsistent_embeddings:

    print()
    print("First inconsistent images:")

    for path in inconsistent_embeddings[:10]:
        print(path)

print()


# ============================================================
# MAP CLEAN OBSERVATIONS TO EMBEDDINGS
# ============================================================

clean_embeddings = []

mapping_rows = []

missing_images = []


for clean_index, row in clean_df.iterrows():

    image_path = row["image_path"]

    if image_path not in image_to_embedding:

        missing_images.append(image_path)

        continue


    embedding = image_to_embedding[image_path]

    clean_embeddings.append(
        embedding
    )

    mapping_rows.append({

        "clean_index": clean_index,
        "storm_id": row["storm_id"],
        "timestamp": row["timestamp"],
        "image_path": image_path,
        "embedding_index": len(clean_embeddings) - 1

    })


# ============================================================
# CHECK MISSING IMAGES
# ============================================================

print("=" * 70)
print("CLEAN DATASET MAPPING")
print("=" * 70)

print(
    "Clean observations:",
    len(clean_df)
)

print(
    "Successfully mapped embeddings:",
    len(clean_embeddings)
)

print(
    "Missing image mappings:",
    len(missing_images)
)


if missing_images:

    print()
    print("First missing images:")

    for path in missing_images[:10]:
        print(path)


# ============================================================
# STOP IF MAPPING IS INCOMPLETE
# ============================================================

if len(clean_embeddings) != len(clean_df):

    raise ValueError(
        "Not every clean observation has an embedding. "
        "Do not continue until this is resolved."
    )


# ============================================================
# CREATE ARRAY
# ============================================================

X_clean = np.stack(
    clean_embeddings
)


# ============================================================
# SAVE
# ============================================================

np.save(
    OUTPUT_EMBEDDINGS,
    X_clean
)


mapping_df = pd.DataFrame(
    mapping_rows
)

mapping_df.to_csv(
    OUTPUT_MAPPING,
    index=False
)


# ============================================================
# FINAL REPORT
# ============================================================

print()
print("=" * 70)
print("CLEAN EMBEDDINGS CREATED")
print("=" * 70)

print(
    "Output embeddings:",
    OUTPUT_EMBEDDINGS
)

print(
    "Output mapping:",
    OUTPUT_MAPPING
)

print(
    "Embedding shape:",
    X_clean.shape
)

print()


# ============================================================
# SANITY CHECK
# ============================================================

print("=" * 70)
print("FINAL SANITY CHECK")
print("=" * 70)

print(
    "NaN values:",
    np.isnan(X_clean).sum()
)

print(
    "Infinite values:",
    np.isinf(X_clean).sum()
)

print(
    "Embedding dimension:",
    X_clean.shape[1]
)

print(
    "Expected observations:",
    len(clean_df)
)

print(
    "Actual embeddings:",
    len(X_clean)
)
