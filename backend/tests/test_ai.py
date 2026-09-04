from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_ai_analyze_endpoint():
    payload = {
        "storm_id": "test-storm-001",
        "timestamp": "2026-09-04T18:00:00Z",
        "wind_kts": 72.0,
        "pressure_hpa": 982.0,
        "previous_wind_kts": 68.0,
        "previous_pressure_hpa": 985.0,
        "satellites": ["INSAT-3D", "Meteosat-5"]
    }
    response = client.post("/api/ai/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["storm_id"] == "test-storm-001"
    assert data["strength_trend"]["label"] == "strengthening"
    assert data["pattern"]["experimental"] is True
    assert "warnings" in data
