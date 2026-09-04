from typing import Optional
from backend.app.schemas.ai import ModelComponentOutput


def predict_next_stage(
    current_pattern_label: Optional[str] = None,
    trend_label: Optional[str] = None
) -> ModelComponentOutput:
    """
    Next-stage cyclone prediction engine.
    Currently implements a persistence baseline (dataset baseline).
    Structured so future trained ML/DL models can seamlessly integrate.
    """
    predicted_label = current_pattern_label if current_pattern_label else "organizing"

    return ModelComponentOutput(
        label=predicted_label,
        confidence=None,
        method="persistence_baseline",
        experimental=True,
    )
