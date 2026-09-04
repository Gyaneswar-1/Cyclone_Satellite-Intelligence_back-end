import pandas as pd
import numpy as np

from sklearn.model_selection import GroupKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression

from sklearn.metrics import accuracy_score, f1_score, confusion_matrix


# ============================================================
# CONFIGURATION
# ============================================================

PREDICTION_DATA = "stormsense_dataset/processed/prediction_observations_v2.csv"

CLEAN_DATA = "stormsense_dataset/processed/clean_observations_v2.csv"

EMBEDDINGS_FILE = "stormsense_dataset/features/X_clean.npy"

MAPPING_FILE = "stormsense_dataset/features/embedding_mapping.csv"


# ============================================================
# LOAD DATA
# ============================================================

prediction_df = pd.read_csv(PREDICTION_DATA)

clean_df = pd.read_csv(CLEAN_DATA)

X_embeddings = np.load(EMBEDDINGS_FILE)

mapping_df = pd.read_csv(MAPPING_FILE)


print("=" * 70)
print("STORMSENSE MULTIMODAL STRENGTH EXPERIMENT")
print("=" * 70)

print("Prediction rows:", len(prediction_df))
print("Clean observations:", len(clean_df))
print("Embedding shape:", X_embeddings.shape)
print("Mapping rows:", len(mapping_df))

print()


# ============================================================
# CONVERT TIMESTAMPS
# ============================================================

prediction_df["timestamp"] = pd.to_datetime(
    prediction_df["timestamp"]
)

clean_df["timestamp"] = pd.to_datetime(
    clean_df["timestamp"]
)

mapping_df["timestamp"] = pd.to_datetime(
    mapping_df["timestamp"]
)


# ============================================================
# PREPARE MAPPING
# ============================================================

# embedding_mapping.csv contains:
#
# clean_index
# storm_id
# timestamp
# image_path
# embedding_index
#
# We use storm_id + timestamp as the observation key.

mapping_df = mapping_df[
    [
        "storm_id",
        "timestamp",
        "image_path",
        "embedding_index"
    ]
].copy()


# ============================================================
# MERGE PREDICTION DATA WITH EMBEDDING MAPPING
# ============================================================

df = prediction_df.merge(
    mapping_df,
    on=[
        "storm_id",
        "timestamp",
        "image_path"
    ],
    how="left",
    validate="one_to_one"
)


# ============================================================
# CHECK MAPPING
# ============================================================

print("=" * 70)
print("EMBEDDING MAPPING CHECK")
print("=" * 70)

print(
    "Prediction rows:",
    len(df)
)

print(
    "Rows with embedding index:",
    df["embedding_index"].notna().sum()
)

print(
    "Rows without embedding index:",
    df["embedding_index"].isna().sum()
)

print()


if df["embedding_index"].isna().any():

    missing = df[
        df["embedding_index"].isna()
    ]

    print("First missing mappings:")
    print(
        missing[
            [
                "storm_id",
                "timestamp",
                "image_path"
            ]
        ].head(10).to_string(index=False)
    )

    raise ValueError(
        "Some prediction observations do not have embeddings."
    )


# ============================================================
# EXTRACT EMBEDDINGS
# ============================================================

embedding_indices = (
    df["embedding_index"]
    .astype(int)
    .to_numpy()
)

X_image = X_embeddings[
    embedding_indices
]


print(
    "Mapped image feature shape:",
    X_image.shape
)

print()


# ============================================================
# CREATE STRENGTH TARGET
# ============================================================

conditions = [

    (
        (df["future_wind_change"] > 0) &
        (df["future_pressure_change"] < 0)
    ),

    (
        (df["future_wind_change"] < 0) &
        (df["future_pressure_change"] > 0)
    )
]

choices = [
    "strengthening",
    "weakening"
]

df["strength_trend"] = np.select(
    conditions,
    choices,
    default="stable"
)


# ============================================================
# CURRENT TREND FOR PERSISTENCE BASELINE
# ============================================================

current_conditions = [

    (
        (df["wind_change"] > 0) &
        (df["pressure_change"] < 0)
    ),

    (
        (df["wind_change"] < 0) &
        (df["pressure_change"] > 0)
    )
]

current_choices = [
    "strengthening",
    "weakening"
]

df["current_trend"] = np.select(
    current_conditions,
    current_choices,
    default="stable"
)


# ============================================================
# KEEP ONLY COMPLETE CURRENT FEATURES
# ============================================================

numerical_features = [
    "wind_kts",
    "pressure_hpa",
    "wind_change",
    "pressure_change"
]

complete_mask = (
    df[numerical_features]
    .notna()
    .all(axis=1)
)

df = df[
    complete_mask
].reset_index(drop=True)

X_image = X_image[
    complete_mask.to_numpy()
]


print("=" * 70)
print("FINAL EXPERIMENT DATA")
print("=" * 70)

print("Rows:", len(df))
print("Storms:", df["storm_id"].nunique())

print()


# ============================================================
# TARGET DISTRIBUTION
# ============================================================

print("=" * 70)
print("STRENGTH TARGET")
print("=" * 70)

print(
    df["strength_trend"].value_counts()
)

print()


# ============================================================
# PREPARE NUMERICAL FEATURES
# ============================================================

X_numeric = df[
    numerical_features
].to_numpy(dtype=float)

y = df[
    "strength_trend"
].to_numpy()

groups = df[
    "storm_id"
].to_numpy()


# ============================================================
# COMBINE IMAGE + NUMERICAL FEATURES
# ============================================================

X_multimodal = np.hstack(
    [
        X_image,
        X_numeric
    ]
)


print("=" * 70)
print("FEATURE SHAPES")
print("=" * 70)

print(
    "Image features:",
    X_image.shape
)

print(
    "Numerical features:",
    X_numeric.shape
)

print(
    "Combined features:",
    X_multimodal.shape
)

print()


# ============================================================
# DEFINE MODELS
# ============================================================

numeric_model = Pipeline([
    (
        "scaler",
        StandardScaler()
    ),

    (
        "classifier",
        LogisticRegression(
            max_iter=3000,
            class_weight="balanced"
        )
    )
])


multimodal_model = Pipeline([
    (
        "scaler",
        StandardScaler()
    ),

    (
        "classifier",
        LogisticRegression(
            max_iter=3000,
            class_weight="balanced"
        )
    )
])


# ============================================================
# CROSS VALIDATION
# ============================================================

gkf = GroupKFold(
    n_splits=5
)


results = {
    "Persistence": {
        "accuracy": [],
        "f1": []
    },

    "Numerical": {
        "accuracy": [],
        "f1": []
    },

    "Multimodal": {
        "accuracy": [],
        "f1": []
    }
}


# Store confusion matrices
confusions = {
    "Numerical": [],
    "Multimodal": []
}


# ============================================================
# RUN FOLDS
# ============================================================

for fold, (train_idx, test_idx) in enumerate(
    gkf.split(
        X_numeric,
        y,
        groups
    ),
    start=1
):

    print()
    print("=" * 70)
    print(f"FOLD {fold}")
    print("=" * 70)

    train_storms = set(
        groups[train_idx]
    )

    test_storms = set(
        groups[test_idx]
    )

    print(
        "Train storms:",
        len(train_storms)
    )

    print(
        "Test storms:",
        len(test_storms)
    )

    print(
        "Overlap:",
        train_storms & test_storms
    )


    # ========================================================
    # TEST DATA
    # ========================================================

    y_test = y[test_idx]


    # ========================================================
    # PERSISTENCE
    # ========================================================

    persistence_pred = (
        df.iloc[test_idx]["current_trend"]
        .to_numpy()
    )

    persistence_accuracy = accuracy_score(
        y_test,
        persistence_pred
    )

    persistence_f1 = f1_score(
        y_test,
        persistence_pred,
        average="macro"
    )

    results["Persistence"]["accuracy"].append(
        persistence_accuracy
    )

    results["Persistence"]["f1"].append(
        persistence_f1
    )


    # ========================================================
    # NUMERICAL MODEL
    # ========================================================

    numeric_model.fit(
        X_numeric[train_idx],
        y[train_idx]
    )

    numeric_pred = numeric_model.predict(
        X_numeric[test_idx]
    )

    numeric_accuracy = accuracy_score(
        y_test,
        numeric_pred
    )

    numeric_f1 = f1_score(
        y_test,
        numeric_pred,
        average="macro"
    )

    results["Numerical"]["accuracy"].append(
        numeric_accuracy
    )

    results["Numerical"]["f1"].append(
        numeric_f1
    )

    confusions["Numerical"].append(
        confusion_matrix(
            y_test,
            numeric_pred,
            labels=[
                "stable",
                "strengthening",
                "weakening"
            ]
        )
    )


    # ========================================================
    # MULTIMODAL MODEL
    # ========================================================

    multimodal_model.fit(
        X_multimodal[train_idx],
        y[train_idx]
    )

    multimodal_pred = multimodal_model.predict(
        X_multimodal[test_idx]
    )

    multimodal_accuracy = accuracy_score(
        y_test,
        multimodal_pred
    )

    multimodal_f1 = f1_score(
        y_test,
        multimodal_pred,
        average="macro"
    )

    results["Multimodal"]["accuracy"].append(
        multimodal_accuracy
    )

    results["Multimodal"]["f1"].append(
        multimodal_f1
    )

    confusions["Multimodal"].append(
        confusion_matrix(
            y_test,
            multimodal_pred,
            labels=[
                "stable",
                "strengthening",
                "weakening"
            ]
        )
    )


    # ========================================================
    # FOLD OUTPUT
    # ========================================================

    print()
    print("Persistence")
    print(
        f"Accuracy: {persistence_accuracy:.4f}"
    )

    print(
        f"Macro F1: {persistence_f1:.4f}"
    )

    print()
    print("Numerical")
    print(
        f"Accuracy: {numeric_accuracy:.4f}"
    )

    print(
        f"Macro F1: {numeric_f1:.4f}"
    )

    print()
    print("Multimodal")
    print(
        f"Accuracy: {multimodal_accuracy:.4f}"
    )

    print(
        f"Macro F1: {multimodal_f1:.4f}"
    )


# ============================================================
# FINAL RESULTS
# ============================================================

print()
print()
print("=" * 70)
print("FINAL MULTIMODAL RESULTS")
print("=" * 70)


for name in [
    "Persistence",
    "Numerical",
    "Multimodal"
]:

    accuracy_values = np.array(
        results[name]["accuracy"]
    )

    f1_values = np.array(
        results[name]["f1"]
    )

    print()
    print(name)

    print(
        f"Mean Accuracy: {accuracy_values.mean():.4f}"
    )

    print(
        f"Accuracy Std: {accuracy_values.std():.4f}"
    )

    print(
        f"Mean Macro F1: {f1_values.mean():.4f}"
    )

    print(
        f"Macro F1 Std: {f1_values.std():.4f}"
    )


# ============================================================
# IMPROVEMENTS
# ============================================================

print()
print("=" * 70)
print("MULTIMODAL IMPROVEMENT")
print("=" * 70)


persistence_accuracy = np.mean(
    results["Persistence"]["accuracy"]
)

persistence_f1 = np.mean(
    results["Persistence"]["f1"]
)

numeric_accuracy = np.mean(
    results["Numerical"]["accuracy"]
)

numeric_f1 = np.mean(
    results["Numerical"]["f1"]
)

multimodal_accuracy = np.mean(
    results["Multimodal"]["accuracy"]
)

multimodal_f1 = np.mean(
    results["Multimodal"]["f1"]
)


print(
    "Multimodal vs Persistence accuracy:",
    f"{multimodal_accuracy - persistence_accuracy:+.4f}"
)

print(
    "Multimodal vs Persistence Macro F1:",
    f"{multimodal_f1 - persistence_f1:+.4f}"
)

print()

print(
    "Multimodal vs Numerical accuracy:",
    f"{multimodal_accuracy - numeric_accuracy:+.4f}"
)

print(
    "Multimodal vs Numerical Macro F1:",
    f"{multimodal_f1 - numeric_f1:+.4f}"
)


# ============================================================
# COMBINED CONFUSION MATRICES
# ============================================================

print()
print("=" * 70)
print("COMBINED CONFUSION MATRICES")
print("=" * 70)

labels = [
    "stable",
    "strengthening",
    "weakening"
]


for name in [
    "Numerical",
    "Multimodal"
]:

    combined_matrix = np.sum(
        confusions[name],
        axis=0
    )

    print()
    print(name)

    confusion_df = pd.DataFrame(
        combined_matrix,
        index=[
            f"Actual {x}"
            for x in labels
        ],
        columns=[
            f"Pred {x}"
            for x in labels
        ]
    )

    print(
        confusion_df
    )
