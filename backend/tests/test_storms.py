from fastapi.testclient import TestClient
import pytest
from backend.app.main import app
from backend.app.providers import get_provider, IMDProvider, MOSDACProvider, NOAAProvider, MockProvider

client = TestClient(app)


def test_get_active_storms():
    response = client.get("/api/storms")
    assert response.status_code == 200
    storms = response.json()
    assert isinstance(storms, list)
    assert len(storms) > 0
    assert "storm_id" in storms[0]
    assert "storm_name" in storms[0]
    assert "active" in storms[0]
    assert "observation_count" in storms[0]


def test_get_storm_detail():
    response = client.get("/api/storms")
    storm_id = response.json()[0]["storm_id"]

    detail_resp = client.get(f"/api/storms/{storm_id}")
    assert detail_resp.status_code == 200
    detail = detail_resp.json()
    assert detail["storm_id"] == storm_id
    assert "latest_observation" in detail


def test_get_storm_observations():
    response = client.get("/api/storms")
    storm_id = response.json()[0]["storm_id"]

    obs_resp = client.get(f"/api/storms/{storm_id}/observations")
    assert obs_resp.status_code == 200
    observations = obs_resp.json()
    assert isinstance(observations, list)
    assert len(observations) > 0
    first_obs = observations[0]
    assert "storm_id" in first_obs
    assert "timestamp" in first_obs
    assert "satellites" in first_obs
    assert isinstance(first_obs["satellites"], list)
    # Check ISO 8601 UTC timestamp ends with Z
    assert first_obs["timestamp"].endswith("Z")


def test_get_storm_track():
    response = client.get("/api/storms")
    storm_id = response.json()[0]["storm_id"]

    track_resp = client.get(f"/api/storms/{storm_id}/track")
    assert track_resp.status_code == 200
    track = track_resp.json()
    assert "track" in track
    assert isinstance(track["track"], list)
    assert len(track["track"]) > 0
    first_pt = track["track"][0]
    assert "lat" in first_pt
    assert "lon" in first_pt
    assert "timestamp" in first_pt
    assert first_pt["timestamp"].endswith("Z")


def test_get_satellite_timeline():
    response = client.get("/api/storms")
    storm_id = response.json()[0]["storm_id"]

    sat_resp = client.get(f"/api/storms/{storm_id}/satellite")
    assert sat_resp.status_code == 200
    sat_data = sat_resp.json()
    assert sat_data["storm_id"] == storm_id
    assert "total_images" in sat_data
    assert "observations" in sat_data
    assert isinstance(sat_data["observations"], list)
    assert len(sat_data["observations"]) > 0


def test_get_satellite_latest():
    response = client.get("/api/storms")
    storm_id = response.json()[0]["storm_id"]

    latest_resp = client.get(f"/api/storms/{storm_id}/satellite/latest")
    assert latest_resp.status_code == 200
    latest = latest_resp.json()
    assert "satellite" in latest
    assert "image_url" in latest
    assert "channel" in latest
    assert latest["timestamp"].endswith("Z")


def test_synthetic_fani_storm():
    detail_resp = client.get("/api/storms/storm-001")
    assert detail_resp.status_code == 200
    assert detail_resp.json()["storm_name"] == "FANI"

    track_resp = client.get("/api/storms/storm-001/track")
    assert track_resp.status_code == 200
    assert len(track_resp.json()["track"]) == 4


def test_nonexistent_storm_404():
    unknown_id = "nonexistent-cyclone-9999"

    resp_detail = client.get(f"/api/storms/{unknown_id}")
    assert resp_detail.status_code == 404

    resp_obs = client.get(f"/api/storms/{unknown_id}/observations")
    assert resp_obs.status_code == 404

    resp_track = client.get(f"/api/storms/{unknown_id}/track")
    assert resp_track.status_code == 404

    resp_sat = client.get(f"/api/storms/{unknown_id}/satellite")
    assert resp_sat.status_code == 404

    resp_sat_latest = client.get(f"/api/storms/{unknown_id}/satellite/latest")
    assert resp_sat_latest.status_code == 404


def test_provider_fallbacks():
    import asyncio

    async def _run():
        # IMD Provider fallback to Mock
        imd = IMDProvider(base_url="http://invalid-imd-domain-test.xyz")
        storms = await imd.get_active_storms()
        assert len(storms) > 0

        obs = await imd.get_observations("storm-001")
        assert len(obs) > 0

        track = await imd.get_track("storm-001")
        assert track is not None

        sat = await imd.get_satellite_timeline("storm-001")
        assert sat is not None

        # MOSDAC Provider fallback to Mock
        mosdac = MOSDACProvider(base_url="http://invalid-mosdac-domain-test.xyz")
        mosdac_storms = await mosdac.get_active_storms()
        assert len(mosdac_storms) > 0

        # NOAA Provider fallback to Mock
        noaa = NOAAProvider(base_url="http://invalid-noaa-domain-test.xyz")
        noaa_storms = await noaa.get_active_storms()
        assert len(noaa_storms) > 0

        # Factory selection
        assert isinstance(get_provider("mock"), MockProvider)
        assert isinstance(get_provider("imd"), IMDProvider)
        assert isinstance(get_provider("mosdac"), MOSDACProvider)
        assert isinstance(get_provider("noaa"), NOAAProvider)

    asyncio.run(_run())

