from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_get_active_storms():
    response = client.get("/api/storms")
    assert response.status_code == 200
    storms = response.json()
    assert isinstance(storms, list)
    assert len(storms) > 0
    assert "storm_id" in storms[0]
    assert "storm_name" in storms[0]


def test_get_storm_detail():
    response = client.get("/api/storms")
    storm_id = response.json()[0]["storm_id"]

    detail_resp = client.get(f"/api/storms/{storm_id}")
    assert detail_resp.status_code == 200
    detail = detail_resp.json()
    assert detail["storm_id"] == storm_id


def test_get_storm_track():
    response = client.get("/api/storms")
    storm_id = response.json()[0]["storm_id"]

    track_resp = client.get(f"/api/storms/{storm_id}/track")
    assert track_resp.status_code == 200
    track = track_resp.json()
    assert "track" in track
    assert isinstance(track["track"], list)
