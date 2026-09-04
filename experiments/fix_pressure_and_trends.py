import pandas as pd
import numpy as np


# ============================================================
# CONFIGURATION
# ============================================================

INPUT_FILE = "Training Overhead/v1_data/clean_observations.csv"
OUTPUT_FILE = "stormsense_dataset/processed/clean_observations_v2.csv"


# ============================================================
# LOAD DATA
# ============================================================

df = pd.read_csv(INPUT_FILE)

df["timestamp"] = pd.to_datetime(df["timestamp"])


print("=" * 70)
print("FIXING PRESSURE DATA AND TEMPORAL FEATURES")
print("=" * 70)

print("Input rows:", len(df))
print("Input storms:", df["storm_id"].nunique())

print()


# ============================================================
# REPLACE SOURCE SENTINEL
# ============================================================

sentinel_count = (
    df["pressure_hpa"] == -999.0
).sum()

print("=" * 70)
print("PRESSURE SENTINEL CHECK")
print("=" * 70)

print(
    "Pressure values equal to -999:",
    sentinel_count
)

print()


# -999 is a missing-data sentinel in this dataset.
df.loc[
    df["pressure_hpa"] == -999.0,
    "pressure_hpa"
] = np.nan


# ============================================================
# SORT CHRONOLOGICALLY
# ============================================================

df = df.sort_values(
    ["storm_id", "timestamp"]
).reset_index(drop=True)


# ============================================================
# RECALCULATE WIND CHANGE
# ============================================================

df["wind_change"] = (
    df.groupby("storm_id")["wind_kts"]
      .diff()
)


# ============================================================
# RECALCULATE PRESSURE CHANGE
# ============================================================

# diff() naturally becomes NaN when either the current
# or previous pressure is missing.
df["pressure_change"] = (
    df.groupby("storm_id")["pressure_hpa"]
      .diff()
)


# ============================================================
# REPLACE ORIGINAL COLUMN ORDER
# ============================================================

df = df[
    [
        "storm_id",
        "storm_name",
        "timestamp",
        "image_path",
        "satellites",
        "wind_kts",
        "pressure_hpa",
        "lat",
        "lon",
        "wind_change",
        "pressure_change",
        "stage"
    ]
]


# ============================================================
# SAVE
# ============================================================

df.to_csv(
    OUTPUT_FILE,
    index=False
)


# ============================================================
# REPORT
# ============================================================

print("=" * 70)
print("CORRECTED DATASET")
print("=" * 70)

print("Output:", OUTPUT_FILE)
print("Rows:", len(df))
print("Storms:", df["storm_id"].nunique())

print()


# ============================================================
# PRESSURE SUMMARY
# ============================================================

print("=" * 70)
print("PRESSURE SUMMARY")
print("=" * 70)

print(
    df["pressure_hpa"].describe()
)

print()


# ============================================================
# MISSING VALUES
# ============================================================

print("=" * 70)
print("MISSING VALUES")
print("=" * 70)

print(
    df.isna().sum()
)

print()


# ============================================================
# TEMPORAL FEATURE SUMMARY
# ============================================================

print("=" * 70)
print("WIND CHANGE SUMMARY")
print("=" * 70)

print(
    df["wind_change"].describe()
)

print()


print("=" * 70)
print("PRESSURE CHANGE SUMMARY")
print("=" * 70)

print(
    df["pressure_change"].describe()
)

print()


# ============================================================
# EXTREME PRESSURE CHANGE CHECK
# ============================================================

print("=" * 70)
print("EXTREME PRESSURE CHANGE CHECK")
print("=" * 70)

extreme = df[
    df["pressure_change"].abs() > 20
]

print(
    "Changes larger than ±20 hPa:",
    len(extreme)
)

if len(extreme) > 0:

    print()

    print(
        extreme[
            [
                "storm_id",
                "timestamp",
                "pressure_hpa",
                "pressure_change"
            ]
        ].to_string(index=False)
    )

else:

    print(
        "GOOD: No pressure changes larger than ±20 hPa."
    )


# ============================================================
# SENTINEL CHECK
# ============================================================

print()
print("=" * 70)
print("FINAL SENTINEL CHECK")
print("=" * 70)

print(
    "Remaining -999 pressure values:",
    (df["pressure_hpa"] == -999.0).sum()
)
