# 🤖 Member 3 Guide — Cyra AI Agent & Grounded RAG System

**Project:** StormSense — Live Cyclone Intelligence (SIH 2026)  
**Assigned Role:** Member 3 (Conversational AI Agent, RAG Pipeline, Tool Integration & Grounding)  
**Primary Focus:** Build, manage, and extend the **Cyra AI Agent** and its **Retrieval-Augmented Generation (RAG)** pipeline to answer user queries with strict source grounding and citation tracking.

---

## 📌 1. Executive Summary & Objective

As **Member 3**, your main objective is to provide a reliable, conversational interface (**Cyra**) for meteorologists and disaster response teams. 

### Key Responsibilities:
1. **Prevent Hallucinations**: Ground all responses in official India Meteorological Department (IMD) documentation and verified historical dataset observations.
2. **Tool-Calling Integration**: Interface with Member 1's Data Provider (`BaseStormProvider`) and Member 2's AI Engine (`analyze_cyclone_observation`) without modifying their core logic.
3. **RAG Vector Search**: Ingest document chunks, generate embeddings, manage the FAISS vector index, and retrieve relevant snippets.
4. **Citation Tracking**: Format and attach verifiable source metadata (`title`, `source`, `url_or_path`, `publication_date`, `section`, `snippet`) to every response.

---

## 📁 2. File Ownership & Directory Layout

You are the primary owner of the following files and directories:

```text
backend/app/
├── rag/
│   ├── retriever.py      # Core RAG Vector Search & Data Store Retriever
│   ├── citations.py      # Citation Formatter & Metadata Builder
│   ├── ingestion/        # Document Chunking & Text Processing
│   └── index/            # FAISS Index Loaders & Management
├── routes/
│   └── chat.py           # API Controller (POST /api/chat) & Tool Executor
└── schemas/
    └── chat.py           # Pydantic Schemas (ChatRequest, ChatResponse, CitationSource)

scripts/
└── build_rag.py          # Offline Vector Indexing & Metadata Generation Script
```

---

## 🛠️ 3. Architecture & Tool-Calling Flow

When a user submits a question to `POST /api/chat`, Cyra executes the following flow:

```
                  ┌──────────────────────────┐
                  │ User Message & storm_id  │
                  └────────────┬─────────────┘
                               │
                               ▼
                    POST /api/chat Controller
                               │
       ┌───────────────────────┼───────────────────────┐
       ▼                       ▼                       ▼
Tool: RAG Search       Tool: Storm Detail       Tool: AI Analysis
(rag_retriever)       (get_provider)          (ai_engine)
       │                       │                       │
       ▼                       ▼                       ▼
Official Documents     Live Coordinates        SigLIP & Trend
 & Past Observations     & Observation History     Model Inferences
       │                       │                       │
       └───────────────────────┼───────────────────────┘
                               │
                               ▼
                   Synthesized Response Generator
                               │
                               ▼
                  Grounded Answer + Citations
```

---

## 🔧 4. Agent Tool Helper Specifications

In `backend/app/routes/chat.py`, five agent tool helpers are pre-built for your use:

| Tool Function | Description | Source Module |
| :--- | :--- | :--- |
| `get_current_storm(storm_id)` | Returns summary details and latest observation for a storm. | `backend.app.providers` |
| `get_recent_observations(storm_id)` | Returns chronological observation history. | `backend.app.providers` |
| `get_satellite_observations(storm_id)` | Returns satellite imagery capture timeline. | `backend.app.providers` |
| `get_ai_analysis(storm_id)` | Triggers Member 2's multimodal AI pipeline (SigLIP + Trend + Baseline). | `backend.app.services.ai_engine` |
| `search_official_sources(query)` | Queries the FAISS vector index & document store for top matched citations. | `backend.app.rag.retriever` |

---

## 📄 5. Data Models & API Contracts (`backend/app/schemas/chat.py`)

### Input Payload (`ChatRequest`)
```json
{
  "message": "Is cyclone FANI strengthening and what is its wind speed?",
  "storm_id": "storm-001"
}
```

### Output Response (`ChatResponse`)
```json
{
  "answer": "Based on StormSense analysis for cyclone 'storm-001', the system detects a strengthening trend with maximum sustained wind speeds of 90.0 kts.\n\n**Official Sources & References:**\n1. [IMD Tropical Cyclone Operational Guidelines](https://mausam.imd.gov.in/) (2024-01-01) - *India Meteorological Department (IMD)*",
  "sources": [
    {
      "title": "IMD Tropical Cyclone Operational Guidelines",
      "source": "India Meteorological Department (IMD)",
      "url_or_path": "https://mausam.imd.gov.in/",
      "publication_date": "2024-01-01",
      "section": "Classification Standard",
      "snippet": "Official IMD cyclone intensity scale categorizes storms based on 3-minute average maximum sustained surface wind speeds."
    }
  ],
  "tools_used": [
    "search_official_sources",
    "get_ai_analysis"
  ],
  "storm_id": "storm-001",
  "disclaimer": "StormSense AI inferences are research outputs and do not replace official IMD bulletins."
}
```

---

## ⚡ 6. How to Build & Re-Index the RAG Vector Store

The offline RAG indexing script is located at `scripts/build_rag.py`. It converts cyclone observations and guidelines into vector embeddings using FAISS.

### Steps to Run Indexing:
1. Activate virtual environment:
   ```bash
   source .venv/bin/activate
   ```
2. Run the offline index builder:
   ```bash
   python3 scripts/build_rag.py
   ```
3. Artifacts generated:
   - Vector Index: `stormsense_dataset/features/rag.index`
   - Document Store Metadata: `stormsense_dataset/features/rag_metadata.json`

---

## 🚀 7. How to Add New Documents or Guidelines

To add official IMD PDF manuals, SOPs, or research papers:

1. **Place raw text/documents** in `stormsense_dataset/raw/` or `backend/app/rag/ingestion/`.
2. **Update `scripts/build_rag.py`** to chunk the text and append entries to `rag_metadata.json`.
3. **Re-run `python3 scripts/build_rag.py`**.
4. The `StormSenseRAGRetriever` in `backend/app/rag/retriever.py` will automatically load the updated index during FastAPI startup.

---

## 🧪 8. Testing & Verification

Run the dedicated Cyra Chat unit test:

```bash
PYTHONPATH=. .venv/bin/pytest backend/tests/test_chat.py
```

### Manual API Test (cURL):
```bash
curl -X POST "http://localhost:8000/api/chat" \
     -H "Content-Type: application/json" \
     -d '{"message": "What is the intensity trend of FANI?", "storm_id": "storm-001"}'
```

---

## ⚠️ Critical Rules for Member 3

1. **Clear Disclaimers**: Always retain the disclaimer: `"StormSense AI inferences are research outputs and do not replace official IMD bulletins."`
2. **Non-Blocking Imports**: Do not directly import PyTorch or heavy model weights inside `chat.py`. Use the exported service wrapper `get_ai_analysis()`.
3. **Graceful Fallbacks**: If the FAISS index is missing or LLM API key is not configured, fallback cleanly to metadata keyword search without throwing HTTP 500 errors.
