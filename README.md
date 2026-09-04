# StormSense — Live Cyclone Intelligence

**Smart India Hackathon (SIH 2026)**  
**Problem Statement:** Development of an AI/ML-based system for identification, classification, and prediction of tropical cyclone patterns using multi-source satellite data.  
**Organization:** Ministry of Earth Sciences (MoES) — India Meteorological Department (IMD).  
**Category:** Software | **Theme:** Disaster Management

---

## 🚀 Overview

StormSense is an integrated live cyclone intelligence platform providing real-time data normalization, satellite imagery timeline rendering, multimodal SigLIP vision feature extraction, deterministic intensity trend modeling, and a grounded RAG-powered AI assistant (**Cyra**).

---

## 📁 Repository Organization

```text
stormsense_dataset/
├── backend/                     # Production FastAPI Application
│   ├── app/                     # Main application logic & endpoints
│   ├── tests/                   # Unit test suite
│   ├── requirements.txt         # Backend Python dependencies
│   ├── .env.example             # Environment configuration template
│   └── README.md                # Detailed backend documentation
├── experiments/                 # Research notebooks & experiment scripts
│   ├── build_clean_embeddings.py
│   ├── fix_pressure_and_trends.py
│   └── test_multimodal_strength.py
├── scripts/                     # Offline utility scripts
│   ├── build_embeddings.py      # SigLIP feature generator script
│   ├── build_rag.py             # FAISS RAG index builder script
│   └── download_data.py         # NOAA HURSAT data downloader script
├── stormsense_dataset/          # Clean dataset & feature store
│   ├── features/                # X_clean.npy & embedding_mapping.csv
│   ├── processed/               # clean_observations_v2.csv & prediction_observations_v2.csv
│   └── raw/                     # Raw archives & extracted NetCDF files
└── Training Overhead/           # Archived baseline & intermediate data
```

---

## ⚡ Getting Started

### 1. Start FastAPI Server
```bash
source .venv/bin/activate
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 2. Access API Documentation
- **Swagger Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Health Check**: [http://localhost:8000/health](http://localhost:8000/health)

### 3. Run Offline Utilities
- **Build SigLIP Embeddings**: `python3 scripts/build_embeddings.py`
- **Build FAISS Index**: `python3 scripts/build_rag.py`

---

## 📜 Scientific Disclaimer

All machine learning outputs (stage labels, next-stage persistence predictions, and trend rules) are prototype research outputs developed for SIH 2026. They are clearly labeled with `"experimental": true` and are **not official IMD cyclone forecasts**. Official tropical cyclone advisories should always be retrieved directly from the [India Meteorological Department](https://mausam.imd.gov.in/).
