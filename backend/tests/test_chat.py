from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_chat_endpoint():
    payload = {
        "message": "Is cyclone FANI strengthening?",
        "storm_id": "storm-001"
    }
    response = client.post("/api/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert "sources" in data
    assert "disclaimer" in data
