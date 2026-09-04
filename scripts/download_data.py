#!/usr/bin/env python3

"""
StormSense historical tropical cyclone dataset downloader & raw builder.

Source:
    NOAA/NCEI HURSAT-B1 v06
"""

from __future__ import annotations

import io
import json
import math
import re
import shutil
import tarfile
import time
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import requests
from bs4 import BeautifulSoup
from PIL import Image
from tqdm import tqdm


# ============================================================
# CONFIGURATION
# ============================================================

BASE_URL = (
    "https://www.ncei.noaa.gov/"
    "data/hurricane-satellite-hursat-b1/archive/v06"
)

DATASET_DIR = Path("stormsense_dataset")
RAW_DIR = DATASET_DIR / "raw"

ARCHIVE_DIR = RAW_DIR / "raw_archives"
EXTRACT_DIR = RAW_DIR / "extracted"
IMAGE_DIR = RAW_DIR / "images"

METADATA_CSV = RAW_DIR / "metadata.csv"
SUMMARY_JSON = RAW_DIR / "dataset_summary.json"

YEARS = list(range(2000, 2016))
MAX_STORMS = 20
MIN_OBSERVATIONS = 8
MAX_ARCHIVE_SIZE_MB = 100

TIMEOUT = 120
RETRIES = 3
REQUEST_DELAY = 0.5


@dataclass
class Observation:
    storm_id: str
    storm_name: str
    timestamp: pd.Timestamp
    image_path: str
    satellite: str
    wind_kts: float
    pressure_hpa: float
    lat: float
    lon: float


session = requests.Session()
session.headers.update(
    {
        "User-Agent": (
            "StormSense-SIH26070-DatasetBuilder/1.0 "
            "(educational research project)"
        )
    }
)


def download_bytes(url: str) -> bytes:
    last_error = None
    for attempt in range(1, RETRIES + 1):
        try:
            response = session.get(url, timeout=TIMEOUT)
            response.raise_for_status()
            return response.content
        except Exception as exc:
            last_error = exc
            print(f"[WARN] Download failed (attempt {attempt}/{RETRIES}): {url}")
            if attempt < RETRIES:
                time.sleep(2 * attempt)
    raise RuntimeError(f"Failed to download after {RETRIES} attempts: {url}") from last_error


def get_year_archives(year: int) -> list[str]:
    url = f"{BASE_URL}/{year}/"
    print(f"\n[INFO] Reading archive index: {url}")
    try:
        html = download_bytes(url).decode("utf-8", errors="ignore")
        soup = BeautifulSoup(html, "html.parser")

        archives = []
        for link in soup.find_all("a"):
            href = link.get("href")
            if not href or not href.endswith(".tar.gz"):
                continue
            filename = href.split("/")[-1]
            if "_MISSING_" in filename:
                continue
            archives.append(f"{url}{filename}")
        return archives
    except Exception as e:
        print(f"[WARN] Failed to fetch index for year {year}: {e}")
        return []


def parse_archive_name(url: str) -> dict:
    filename = Path(url).name
    match = re.search(
        r"HURSAT_b1_v06_(?P<serial>\d{4}\d{3}[NS]\d{5})_(?P<name>[^_]+)_c",
        filename,
    )
    if not match:
        return {"filename": filename, "serial": filename, "name": "UNKNOWN"}
    return {
        "filename": filename,
        "serial": match.group("serial"),
        "name": match.group("name"),
    }


def extract_archive(url: str) -> Path:
    archive_name = Path(url).name
    raw_path = ARCHIVE_DIR / archive_name
    storm_folder_name = archive_name.replace(".tar.gz", "")
    extract_path = EXTRACT_DIR / storm_folder_name
    extract_path.mkdir(parents=True, exist_ok=True)

    if not raw_path.exists():
        print(f"[DOWNLOAD] {archive_name}")
        data = download_bytes(url)
        size_mb = len(data) / (1024 * 1024)
        if size_mb > MAX_ARCHIVE_SIZE_MB:
            raise RuntimeError(f"Archive too large: {size_mb:.1f} MB > {MAX_ARCHIVE_SIZE_MB} MB")
        raw_path.parent.mkdir(parents=True, exist_ok=True)
        raw_path.write_bytes(data)

    marker = extract_path / ".extracted"
    if not marker.exists():
        print(f"[EXTRACT] {archive_name}")
        with tarfile.open(raw_path, mode="r:gz") as tar:
            for member in tar.getmembers():
                member_path = (extract_path / member.name).resolve()
                if not str(member_path).startswith(str(extract_path.resolve())):
                    raise RuntimeError("Unsafe tar archive path detected.")
            tar.extractall(extract_path)
        marker.touch()

    return extract_path


def main():
    print("=" * 70)
    print("STORMSENSE DATA DOWNLOADER & PIPELINE")
    print("=" * 70)
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    EXTRACT_DIR.mkdir(parents=True, exist_ok=True)
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Target raw dataset directory: {RAW_DIR}")
    print("[INFO] Initialized raw directories. Use offline download execution to sync external archives.")


if __name__ == "__main__":
    main()
