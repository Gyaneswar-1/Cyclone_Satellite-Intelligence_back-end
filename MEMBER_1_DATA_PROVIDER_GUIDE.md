# 🌐 Member 1 Guide — Live Data Providers & Satellite Layer

**Project:** StormSense — Live Cyclone Intelligence (SIH 2026)  
**Assigned Role:** Member 1 (Data Engineering, Live Provider Adapters, Map Data Normalization)  
**Primary Focus:** Implement, manage, and extend live meteorological data provider adapters (IMD, MOSDAC/ISRO, NOAA) and satellite imagery timelines, ensuring clean spatial-temporal data for the MapLibre frontend.

---

## 📌 1. Executive Summary & Objective

As **Member 1**, your main objective is to establish robust data pipelines connecting external weather APIs and historical satellite databases to the StormSense FastAPI backend.

### Key Responsibilities:
1. **Provider Abstraction**: Implement `BaseStormProvider` adapters for IMD, MOSDAC, NOAA, and synthetic/dataset fallback (`MockProvider`).
2. **Data Normalization**: Standardize raw data from different APIs into clean Pydantic schemas (`StormDetail`, `StormObservation`, `StormTrack`, `SatelliteObservation`).
3. **MapLibre Compatibility**: Produce clean geographic coordinate tracks (`lat`, `lon`, `wind_kts`, `pressure_hpa`) ready for frontend map rendering.
4. **Fail-Safe Fallbacks**: Ensure that if live IMD/MOSDAC servers are unreachable or offline during hackathon evaluations, the system automatically falls back to `MockProvider` without throwing errors.

---

## 📁 2. File Ownership & Directory Layout

You are the primary owner of the following files and directories:

```text
backend/app/
├── providers/
│   ├── base.py          # Abstract Base Class (BaseStormProvider)
│   ├── mock.py          # MockProvider (Dataset CSV & Synthetic fallback)
│   ├── imd.py           # India Meteorological Department (IMD) Adapter
│   ├── mosdac.py        # MOSDAC / ISRO Satellite Feed Adapter
│   ├── noaa.py          # NOAA HURSAT Archive Adapter
│   └── __init__.py      # Provider Factory (get_provider())
├── routes/
│   ├── storms.py        # API Controller (/api/storms)
│   └── satellite.py     # API Controller (/api/storms/{id}/satellite)
└── schemas/
    ├── storm.py         # Pydantic Schemas (StormDetail, StormObservation, StormTrack)
    └── satellite.py     # Pydantic Schemas (SatelliteObservation, SatelliteTimeline)
```

---

## 🛠️ 3. Core Provider Interface (`BaseStormProvider`)

All providers MUST inherit from `BaseStormProvider` in `backend/app/providers/base.py`:

```python
from abc import ABC, abstractmethod
from typing import List, Optional
from backend.app.schemas.storm import StormDetail, StormObservation, StormTrack
from backend.app.schemas.satellite import SatelliteTimeline

class BaseStormProvider(ABC):

    @abstractmethod
    async def get_active_storms(self) -> List[StormDetail]:
        """Fetch list of active cyclones."""
        pass

    @abstractmethod
    async def get_storm_detail(self, storm_id: str) -> Optional[StormDetail]:
        """Fetch summary detail for a specific cyclone."""
        pass

    @abstractmethod
    async def get_observations(self, storm_id: str) -> List[StormObservation]:
        """Fetch chronological observations for a cyclone."""
        pass

    @abstractmethod
    async def get_track(self, storm_id: str) -> Optional[StormTrack]:
        """Fetch spatial coordinates and intensity points for MapLibre map rendering."""
        pass

    @abstractmethod
    async def get_satellite_timeline(self, storm_id: str) -> Optional[SatelliteTimeline]:
        """Fetch satellite imagery observations timeline."""
        pass
```

---

## 📄 4. Pydantic Schemas & Data Contracts

### `StormObservation` (`backend/app/schemas/storm.py`)
```json
{
  "storm_id": "storm-001",
  "storm_name": "FANI",
  "timestamp": "2026-09-04T18:00:00Z",
  "lat": 18.42,
  "lon": 85.13,
  "wind_kts": 90.0,
  "pressure_hpa": 960.0,
  "image_url": "http://localhost:8000/static/sample.jpg",
  "satellites": ["INSAT-3D", "Meteosat-5"],
  "stage": "mature"
}
```

### `StormTrack` (`backend/app/schemas/storm.py`)
```json
{
  "storm_id": "storm-001",
  "storm_name": "FANI",
  "track": [
    {
      "timestamp": "2026-09-04T06:00:00Z",
      "lat": 16.5,
      "lon": 84.1,
      "wind_kts": 65.0,
      "pressure_hpa": 985.0,
      "stage": "organizing"
    },
    {
      "timestamp": "2026-09-04T18:00:00Z",
      "lat": 18.42,
      "lon": 85.13,
      "wind_kts": 90.0,
      "pressure_hpa": 960.0,
      "stage": "mature"
    }
  ]
}
```

---

## 🚀 5. How to Implement a Live Provider Adapter

To connect a new live API (e.g. IMD or MOSDAC):

1. **Open `backend/app/providers/imd.py`** (or `mosdac.py`).
2. **Use `httpx.AsyncClient`** for non-blocking HTTP requests.
3. **Wrap external requests in a `try...except` block** and log warnings using `logger.warning()`.
4. **Fallback to `self.fallback_provider`** (`MockProvider`) if the connection fails or returns non-200 status.

### Example Provider Pattern:
```python
import httpx
from backend.app.providers.base import BaseStormProvider
from backend.app.providers.mock import MockProvider
from backend.app.utils.logging import logger

class IMDProvider(BaseStormProvider):
    def __init__(self, base_url: str = "https://api.imd.gov.in"):
        self.base_url = base_url.rstrip("/")
        self.fallback_provider = MockProvider()

    async def get_active_storms(self):
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{self.base_url}/cyclone/active")
                if resp.status_code == 200:
                    data = resp.json()
                    # Transform raw IMD JSON to List[StormDetail]
                    return [ ... ]
        except Exception as e:
            logger.warning(f"[IMDProvider] API unavailable ({e}). Falling back to MockProvider.")

        return await self.fallback_provider.get_active_storms()
```

---

## ⚙️ 6. Provider Switching & Environment Variables

Provider selection is controlled via `.env`:

```bash
# Data Provider Selection: "mock", "imd", "mosdac", or "noaa"
DATA_PROVIDER=mock

# Live Provider Base URLs
IMD_BASE_URL=https://api.imd.gov.in
MOSDAC_BASE_URL=https://mosdac.gov.in/api
NOAA_BASE_URL=https://www.ncei.noaa.gov/data/hurricane-satellite-hursat-b1/archive/v06
```

The factory function `get_provider()` in `backend/app/providers/__init__.py` reads `DATA_PROVIDER` automatically.

---

## 🧪 7. Testing & Endpoints Summary

### Endpoints Maintained by Member 1:

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/storms` | Active & available cyclone list |
| `GET` | `/api/storms/{id}` | Summary detail for a single cyclone |
| `GET` | `/api/storms/{id}/observations` | Chronological observation list |
| `GET` | `/api/storms/{id}/track` | Spatial-temporal track for MapLibre map |
| `GET` | `/api/storms/{id}/satellite` | Satellite timeline |
| `GET` | `/api/storms/{id}/satellite/latest` | Latest satellite observation metadata |

### Unit Testing:
```bash
PYTHONPATH=. .venv/bin/pytest backend/tests/test_storms.py
```

### Manual cURL Test:
```bash
curl http://localhost:8000/api/storms
curl http://localhost:8000/api/storms/storm-001/track
```

---

## ⚠️ Critical Rules for Member 1

1. **Isolation**: Do NOT import PyTorch, Transformers, or AI model dependencies into `backend/app/providers/`.
2. **Fallback Safety**: Never let an external network error crash an API endpoint. Always catch HTTP exceptions and return data from `MockProvider`.
3. **Time Formatting**: Return all timestamps in standard ISO 8601 UTC format (e.g. `2026-09-04T18:00:00Z`).
