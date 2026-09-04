from typing import Optional
from backend.app.schemas.ai import ModelComponentOutput


def compute_strength_trend(
    current_wind: Optional[float],
    previous_wind: Optional[float],
    current_pressure: Optional[float],
    previous_pressure: Optional[float],
) -> ModelComponentOutput:
    """
    Deterministic rule-based trend engine evaluating direction of intensity changes.
    Rules:
      - wind increasing + pressure decreasing => strengthening
      - wind decreasing + pressure increasing => weakening
      - otherwise => stable
    """
    wind_delta = None
    if current_wind is not None and previous_wind is not None:
        wind_delta = current_wind - previous_wind

    pressure_delta = None
    if current_pressure is not None and previous_pressure is not None:
        pressure_delta = current_pressure - previous_pressure

    if wind_delta is not None and pressure_delta is not None:
        if wind_delta > 0 and pressure_delta < 0:
            label = "strengthening"
        elif wind_delta < 0 and pressure_delta > 0:
            label = "weakening"
        else:
            label = "stable"
    elif wind_delta is not None:
        if wind_delta > 0:
            label = "strengthening"
        elif wind_delta < 0:
            label = "weakening"
        else:
            label = "stable"
    elif pressure_delta is not None:
        if pressure_delta < 0:
            label = "strengthening"
        elif pressure_delta > 0:
            label = "weakening"
        else:
            label = "stable"
    else:
        label = "stable"

    return ModelComponentOutput(
        label=label,
        confidence=None,
        method="wind_pressure_direction_rule",
        experimental=False,
    )
