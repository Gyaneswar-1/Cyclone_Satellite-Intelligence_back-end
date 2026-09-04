from fastapi import APIRouter, HTTPException

from backend.app.schemas.ai import AIAnalysisRequest, AIAnalysisResponse
from backend.app.services.ai_engine import analyze_cyclone_observation

router = APIRouter(prefix="/api/ai", tags=["AI Engine"])


@router.post("/analyze", response_model=AIAnalysisResponse, summary="Perform Multimodal AI Analysis")
async def analyze_cyclone(request: AIAnalysisRequest):
    """
    Analyzes cyclone observations using SigLIP visual feature extraction,
    deterministic trend evaluation, and stage prediction baselines.
    Outputs are experimental prototype research results and not official IMD forecasts.
    """
    try:
        return await analyze_cyclone_observation(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI analysis engine error: {str(e)}")
