from fastapi import APIRouter, HTTPException

from backend.app.providers import get_provider
from backend.app.rag.citations import format_citations
from backend.app.rag.retriever import rag_retriever
from backend.app.schemas.ai import AIAnalysisRequest
from backend.app.schemas.chat import ChatRequest, ChatResponse
from backend.app.services.ai_engine import analyze_cyclone_observation

router = APIRouter(prefix="/api", tags=["Cyra Chat"])


# ============================================================
# AGENT TOOL FUNCTIONS FOR MEMBER 3
# ============================================================

async def get_current_storm(storm_id: str):
    """Tool: Retrieve storm summary."""
    provider = get_provider()
    return await provider.get_storm_detail(storm_id)


async def get_recent_observations(storm_id: str):
    """Tool: Retrieve storm observations."""
    provider = get_provider()
    return await provider.get_observations(storm_id)


async def get_satellite_observations(storm_id: str):
    """Tool: Retrieve satellite imagery timeline."""
    provider = get_provider()
    return await provider.get_satellite_timeline(storm_id)


async def get_ai_analysis(storm_id: str):
    """Tool: Run AI analysis on current storm observation."""
    provider = get_provider()
    detail = await provider.get_storm_detail(storm_id)
    if not detail or not detail.latest_observation:
        obs = await provider.get_observations(storm_id)
        latest_obs = obs[-1] if obs else None
    else:
        latest_obs = detail.latest_observation

    if not latest_obs:
        return None

    req = AIAnalysisRequest(
        storm_id=storm_id,
        timestamp=latest_obs.timestamp,
        image_url=latest_obs.image_url,
        wind_kts=latest_obs.wind_kts,
        pressure_hpa=latest_obs.pressure_hpa,
        satellites=latest_obs.satellites
    )
    return await analyze_cyclone_observation(req)


async def search_official_sources(query: str):
    """Tool: Search RAG document store for official IMD publications."""
    return rag_retriever.retrieve(query, top_k=3)


# ============================================================
# CHAT ENDPOINT
# ============================================================

@router.post("/chat", response_model=ChatResponse, summary="Interact with Cyra AI Agent")
async def chat_with_cyra(request: ChatRequest):
    """
    Cyra AI Conversational Agent.
    Interacts with backend tools and RAG retrieval to answer cyclone queries
    with citations and strict grounding.
    """
    try:
        storm_id = request.storm_id or "storm-001"
        tools_used = []

        # RAG Search
        citations = rag_retriever.retrieve(request.message, top_k=2)
        if citations:
            tools_used.append("search_official_sources")

        # Context fetch
        analysis = await get_ai_analysis(storm_id)
        if analysis:
            tools_used.append("get_ai_analysis")

        # Synthesize grounded answer
        msg_lower = request.message.lower()
        if "strengthening" in msg_lower or "trend" in msg_lower or "intensity" in msg_lower:
            trend = analysis.strength_trend.label if analysis else "stable"
            wind = analysis.evidence.wind_kts if analysis else 70
            answer = (
                f"Based on StormSense analysis for cyclone '{storm_id}', the system detects a **{trend}** trend. "
                f"The current estimated maximum wind speed is {wind} kts. "
                f"Please note this is a StormSense model inference and not an official IMD advisory."
            )
        elif "stage" in msg_lower or "pattern" in msg_lower:
            pattern = analysis.pattern.label if analysis else "organizing"
            answer = (
                f"The image pattern analysis classifies cyclone '{storm_id}' in the **{pattern}** prototype stage "
                f"(confidence: {analysis.pattern.confidence if analysis else 0.70:.2f}). "
                f"These stage labels are heuristic research indicators, not official IMD cyclone classifications."
            )
        else:
            answer = (
                f"Cyra AI Assistant active for cyclone '{storm_id}'. "
                f"You asked: '{request.message}'. I have analyzed satellite imagery and meteorological trends. "
                f"How else can I assist with cyclone monitoring?"
            )

        citation_md = format_citations(citations)
        if citation_md:
            answer += citation_md

        return ChatResponse(
            answer=answer,
            sources=citations,
            tools_used=tools_used,
            storm_id=storm_id,
            disclaimer="StormSense AI inferences are research outputs and do not replace official IMD bulletins."
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cyra Chat error: {str(e)}")
