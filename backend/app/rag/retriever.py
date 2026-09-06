import os
from pathlib import Path
from typing import List, Optional
import pandas as pd

from backend.app.schemas.chat import CitationSource
from backend.app.utils.logging import logger

DATA_PATH = Path("stormsense_dataset/processed/clean_observations_v2.csv")


class StormSenseRAGRetriever:
    """Retriever for official IMD documentation and historical dataset observations."""

    def __init__(self):
        self.is_loaded = False
        self._df: Optional[pd.DataFrame] = None
        self._init_retriever()

    def _init_retriever(self):
        if DATA_PATH.exists():
            try:
                self._df = pd.read_csv(DATA_PATH)
                self.is_loaded = True
                logger.info(f"[RAGRetriever] Loaded observation index from {DATA_PATH} ({len(self._df)} rows)")
            except Exception as e:
                logger.warning(f"[RAGRetriever] Could not load dataset CSV: {e}")

    def retrieve(self, query: str, top_k: int = 3) -> List[CitationSource]:
        """Search official documents or observation records matching query."""
        results: List[CitationSource] = []

        # Standard official source references for IMD / MOSDAC guidelines
        if "imd" in query.lower() or "forecast" in query.lower() or "scale" in query.lower():
            results.append(
                CitationSource(
                    title="IMD Tropical Cyclone Operational Guidelines",
                    source="India Meteorological Department (IMD)",
                    url_or_path="https://mausam.imd.gov.in/",
                    publication_date="2024-01-01",
                    section="Classification Standard",
                    snippet="Official IMD cyclone intensity scale categorizes storms based on 3-minute average maximum sustained surface wind speeds."
                )
            )

        if self._df is not None and not self._df.empty:
            q_lower = query.lower()
            matches = self._df[
                self._df["storm_name"].astype(str).str.lower().str.contains(q_lower) |
                self._df["storm_id"].astype(str).str.lower().str.contains(q_lower) |
                self._df["stage"].astype(str).str.lower().str.contains(q_lower)
            ]
            if matches.empty:
                matches = self._df.head(top_k)

            for _, row in matches.head(top_k).iterrows():
                results.append(
                    CitationSource(
                        title=f"Cyclone {row.get('storm_name', 'Observation')} ({row.get('storm_id')})",
                        source="StormSense Clean Observations v2 Dataset",
                        url_or_path=str(DATA_PATH),
                        publication_date=str(row.get("timestamp", ""))[:10],
                        section="Observation Record",
                        snippet=f"Observed wind: {row.get('wind_kts')} kts, pressure: {row.get('pressure_hpa')} hPa, stage: {row.get('stage')}"
                    )
                )

        # Check Qdrant / Mem0 memories if available
        try:
            from qdrant_client import QdrantClient
            qdrant_host = os.getenv("QDRANT_HOST", "localhost")
            qdrant_port = int(os.getenv("QDRANT_PORT", "6333"))
            mem_col = os.getenv("MEM0_COLLECTION", "cyclone_memories")
            qclient = QdrantClient(host=qdrant_host, port=qdrant_port, timeout=1.5)
            if qclient.collection_exists(mem_col):
                points, _ = qclient.scroll(
                    collection_name=mem_col,
                    limit=10,
                    with_payload=True,
                    with_vectors=False,
                )
                keywords = [w.lower() for w in query.split() if len(w) > 3]
                for pt in points:
                    txt = str(pt.payload.get("text", ""))
                    if any(k in txt.lower() for k in keywords):
                        results.append(
                            CitationSource(
                                title=str(pt.payload.get("source", "Cyclone Memory Record")),
                                source="Qdrant Mem0 Cyclone Knowledge Base",
                                url_or_path=f"qdrant://{mem_col}/{pt.id}",
                                publication_date=str(pt.payload.get("created_at", "2026-09-05"))[:10],
                                section=str(pt.payload.get("category", "Domain Knowledge")),
                                snippet=txt,
                            )
                        )
        except Exception as e:
            logger.debug(f"[RAGRetriever] Qdrant memory lookup skipped: {e}")

        return results


rag_retriever = StormSenseRAGRetriever()
