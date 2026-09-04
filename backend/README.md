# StormSense — Live Cyclone Intelligence FastAPI Backend

**Smart India Hackathon (SIH 2026)**  
**Problem Statement:** Development of an AI/ML-based system for identification, classification, and prediction of tropical cyclone patterns using multi-source satellite data.  
**Organization:** Ministry of Earth Sciences (MoES) — India Meteorological Department (IMD).

---

## 🏛️ System Architecture

The backend serves as the unified integration layer between data sources, AI models, agent frameworks, and the MapLibre frontend:

```
IMD / MOSDAC / Fallback Data Sources
                 │
                 ▼
          Provider Adapters
                 │
                 ▼
     FastAPI Normalization Layer
                 │
        ┌────────┴────────┐
        ▼                 ▼
   Storm APIs      Satellite APIs
        │                 │
        └────────┬────────┘
                 │
                 ▼
              AI Engine
        ┌────────┴────────┐
        ▼                 ▼
      SigLIP        Trend Engine
        │                 │
        └────────┬────────┘
                 │
                 ▼
              Cyra AI
                 │
                 ▼
             FAISS RAG
                 │
                 ▼
             Frontend
```

---

## 📁 Directory Structure

```text
backend/
├── app/
│   ├── main.py                  # FastAPI Application Entry & Lifespan handler
│   ├── routes/                  # API Route Controllers
│   │   ├── health.py            # GET / & GET /health
│   │   ├── storms.py            # Storm endpoints (/api/storms)
│   │   ├── satellite.py         # Satellite imagery timeline (/api/storms/{id}/satellite)
│   │   ├── ai.py                # AI Analysis endpoint (POST /api/ai/analyze)
│   │   └── chat.py              # Cyra AI Agent (POST /api/chat)
│   ├── schemas/                 # Pydantic Request & Response Contracts
│   ├── services/                # Business & Model Engines
│   │   ├── ai_engine.py         # SigLIP vision model manager & pipeline
│   │   ├── trend_engine.py      # Deterministic intensity trend rule engine
│   │   └── prediction_engine.py # Persistence prediction baseline
│   ├── providers/               # Provider Abstraction Layer
│   │   ├── base.py              # BaseStormProvider Abstract Class
│   │   ├── mock.py              # MockProvider (Dataset & synthetic fallback)
│   │   ├── imd.py               # IMD Provider Adapter
│   │   ├── mosdac.py            # MOSDAC/ISRO Provider Adapter
│   │   └── noaa.py              # NOAA Provider Adapter
│   ├── rag/                     # RAG & Citation Tracking
│   │   ├── retriever.py         # FAISS & document retriever
│   │   ├── citations.py         # Citation formatting utility
│   │   ├── ingestion/           # Chunking & ingestion
│   │   └── index/               # FAISS index storage
│   └── utils/                   # Helpers (logging, time, image processing)
├── tests/                       # Pytest unit tests
├── requirements.txt             # Dependencies
├── .env.example                 # Environment configuration template
└── README.md                    # Backend Documentation
```

---

## 👥 Team Member Integration Contracts

### Member 1 (Live Data & Satellite Feed Layer)
- **Scope**: `backend/app/providers/` and `backend/app/routes/storms.py`, `satellite.py`.
- **Contract**: Implement `BaseStormProvider` adapters without touching AI model code. Data is normalized to standard Pydantic schemas (`StormDetail`, `StormObservation`, `StormTrack`).
- **Endpoint Test**: `GET /api/storms`

### Member 2 (AI Engine & Vision Layer)
- **Scope**: `backend/app/services/` and `backend/app/routes/ai.py`.
- **Contract**: Manages SigLIP model (`google/siglip-base-patch16-224`) loaded **ONCE** at startup. Provides intensity trend rules and prototype stage classification (`developing`, `organizing`, `mature`, `weakening`, `ambiguous`). All outputs include `"experimental": true` disclaimers.
- **Endpoint Test**: `POST /api/ai/analyze`

### Member 3 (Cyra AI Agent & RAG Layer)
- **Scope**: `backend/app/rag/` and `backend/app/routes/chat.py`.
- **Contract**: Builds conversational interface using tool function helpers (`get_current_storm`, `get_ai_analysis`, `search_official_sources`) without directly importing PyTorch or SigLIP internals.
- **Endpoint Test**: `POST /api/chat`

---

## ⚙️ Environment Configuration

Copy `.env.example` to `.env` in the backend root:

```bash
cp backend/.env.example backend/.env
```

Key environment variables:
- `DATA_PROVIDER`: `mock` (default offline hackathon mode) or `imd` / `mosdac` / `noaa`
- `ENABLE_VISION_MODEL`: `true` / `false` (allows running server on light RAM without PyTorch vision GPU overhead)
- `SIGLIP_MODEL_ID`: `google/siglip-base-patch16-224`

---

## 🚀 Quickstart & Running FastAPI

1. **Activate Virtual Environment**:
   ```bash
   source .venv/bin/activate
   ```

2. **Start Backend Server**:
   ```bash
   uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

3. **Open Interactive API Documentation**:
   - Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
   - ReDoc UI: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## 🧪 Running Unit Tests

Run automated test suite using `pytest`:

```bash
pytest backend/tests/
```

---

## ⚠️ Scientific & Regulatory Disclaimers

1. Prototype lifecycle stage labels (`developing`, `organizing`, `mature`, `weakening`, `ambiguous`) are heuristic research classifications, **not official IMD intensity categories**.
2. Next-stage predictions are persistence baseline evaluations.
3. All AI responses state explicitly: `"Prototype research output; not an official IMD forecast."`
