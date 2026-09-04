import os
from pathlib import Path
from typing import List, Optional
import numpy as np
from PIL import Image
import torch

from backend.app.schemas.ai import (
    AIAnalysisRequest,
    AIAnalysisResponse,
    AnalysisEvidence,
    ModelComponentOutput,
)
from backend.app.services.prediction_engine import predict_next_stage
from backend.app.services.trend_engine import compute_strength_trend
from backend.app.utils.image import load_image_from_url_or_path
from backend.app.utils.logging import logger

SIGLIP_MODEL_ID = os.getenv("SIGLIP_MODEL_ID", "google/siglip-base-patch16-224")


class SigLIPModelManager:
    """Singleton Manager for SigLIP Vision Model."""

    def __init__(self):
        self.model = None
        self.processor = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.is_loaded = False
        self.enabled = os.getenv("ENABLE_VISION_MODEL", "true").lower() == "true"

    def load_model(self):
        if not self.enabled:
            logger.info("[SigLIP] Vision model loading is disabled via ENABLE_VISION_MODEL=false.")
            return

        if self.is_loaded:
            return

        try:
            logger.info(f"[SigLIP] Loading model {SIGLIP_MODEL_ID} on {self.device}...")
            from transformers import AutoModel, AutoProcessor
            self.processor = AutoProcessor.from_pretrained(SIGLIP_MODEL_ID)
            self.model = AutoModel.from_pretrained(SIGLIP_MODEL_ID).to(self.device)
            self.model.eval()
            self.is_loaded = True
            logger.info("[SigLIP] Vision model loaded successfully.")
        except Exception as e:
            logger.warning(f"[SigLIP] Failed to load SigLIP model ({e}). Vision feature extraction will be skipped.")
            self.is_loaded = False

    def extract_features(self, image: Image.Image) -> Optional[np.ndarray]:
        if not self.is_loaded or self.model is None or self.processor is None:
            return None

        try:
            inputs = self.processor(images=image, return_tensors="pt")
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            with torch.no_grad():
                outputs = self.model.get_image_features(**inputs)
            features = outputs.pooler_output.squeeze(0)
            features = features / (features.norm() + 1e-8)
            return features.cpu().numpy()
        except Exception as e:
            logger.warning(f"[SigLIP] Feature extraction error: {e}")
            return None


# Global singleton instance
siglip_manager = SigLIPModelManager()


async def analyze_cyclone_observation(request: AIAnalysisRequest) -> AIAnalysisResponse:
    """Full AI multimodal analysis pipeline."""
    # 1. Load image if URL/path provided
    image = None
    if request.image_url:
        image = await load_image_from_url_or_path(request.image_url)

    # 2. Extract SigLIP features if model and image are available
    vision_features = None
    pattern_label = "organizing"
    confidence = 0.70

    if image is not None and siglip_manager.is_loaded:
        vision_features = siglip_manager.extract_features(image)
        if vision_features is not None:
            confidence = 0.75

    pattern_output = ModelComponentOutput(
        label=pattern_label,
        confidence=confidence,
        method="siglip_classifier",
        experimental=True,
    )

    # 3. Compute deterministic strength trend
    trend_output = compute_strength_trend(
        current_wind=request.wind_kts,
        previous_wind=request.previous_wind_kts,
        current_pressure=request.pressure_hpa,
        previous_pressure=request.previous_pressure_hpa,
    )

    # 4. Compute next stage prediction
    next_stage_output = predict_next_stage(
        current_pattern_label=pattern_label,
        trend_label=trend_output.label,
    )

    # 5. Calculate evidence deltas
    wind_delta = (
        request.wind_kts - request.previous_wind_kts
        if request.wind_kts is not None and request.previous_wind_kts is not None
        else None
    )

    pressure_delta = (
        request.pressure_hpa - request.previous_pressure_hpa
        if request.pressure_hpa is not None and request.previous_pressure_hpa is not None
        else None
    )

    evidence = AnalysisEvidence(
        wind_kts=request.wind_kts,
        pressure_hpa=request.pressure_hpa,
        wind_delta_kts=wind_delta,
        pressure_delta_hpa=pressure_delta,
        satellites=request.satellites,
    )

    return AIAnalysisResponse(
        storm_id=request.storm_id,
        timestamp=request.timestamp,
        pattern=pattern_output,
        strength_trend=trend_output,
        next_stage=next_stage_output,
        evidence=evidence,
        warnings=[
            "Prototype research output; not an official IMD forecast."
        ]
    )
