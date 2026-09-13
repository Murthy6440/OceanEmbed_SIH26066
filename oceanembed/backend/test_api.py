"""
Quick functional test for every OceanEmbed SIH26066 endpoint.
Run with: python test_api.py
"""
import json

from fastapi.testclient import TestClient

from main import app


def show(name, resp):
    print(f"\n=== {name} -> HTTP {resp.status_code} ===")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    print(json.dumps(data, indent=2)[:800])
    return data


def main(client):
    show("GET /health", client.get("/health"))

    locs = show("GET /api/locations", client.get("/api/locations"))
    assert len(locs["locations"]) > 0

    grid = show("GET /api/grid?resolution=5", client.get("/api/grid?resolution=5"))
    assert "sst" in grid["fields"]
    assert len(grid["lat"]) * len(grid["lon"]) == len(grid["fields"]["sst"]) * len(grid["fields"]["sst"][0])

    loc_id = locs["locations"][0]["location_id"]
    profile = show(f"GET /api/profile/{loc_id}", client.get(f"/api/profile/{loc_id}"))
    assert len(profile["depth_m"]) == len(profile["predicted_temperature_degC"])

    show("GET /api/profile/BAD-ID (expect 404)", client.get("/api/profile/BAD-ID")) \
        if False else None
    r404 = client.get("/api/profile/BAD-ID")
    print(f"\n=== GET /api/profile/BAD-ID -> HTTP {r404.status_code} (expect 404) ===")
    assert r404.status_code == 404

    pred = show(
        "POST /api/predict (lat/lon/depth only)",
        client.post("/api/predict", json={"lat": 15.0, "lon": 70.0, "depth": 200.0}),
    )
    assert "predicted_temperature_degC" in pred
    assert "disclaimer" in pred

    pred2 = show(
        "POST /api/predict (with surface overrides)",
        client.post("/api/predict", json={
            "lat": 12.0, "lon": 85.0, "depth": 500.0,
            "surface_temp": 29.0, "surface_sal": 33.5,
        }),
    )
    assert "surface_temp" in pred2
    assert pred2["surface_inputs_used"]["sst"] == 29.0

    r_bad = client.post("/api/predict", json={"lat": 90.0, "lon": 70.0, "depth": 100.0})
    print(f"\n=== POST /api/predict lat=90 out-of-domain -> HTTP {r_bad.status_code} (expect 422) ===")
    assert r_bad.status_code == 422

    r_shallow = client.post("/api/predict", json={"lat": 8.0, "lon": 47.5, "depth": 500.0})
    print(f"\n=== POST /api/predict near-land too-deep -> HTTP {r_shallow.status_code} (expect 400) ===")
    assert r_shallow.status_code == 400

    surface = show(
        "GET /api/surface?lat=15&lon=70&date=2024-01-15T12:00:00",
        client.get("/api/surface?lat=15&lon=70&date=2024-01-15T12:00:00"),
    )
    assert "surface_fields" in surface
    assert "errors" in surface
    assert isinstance(surface["surface_fields"]["sst"], (int, float))

    val = show("GET /api/validation", client.get("/api/validation"))
    assert "temperature" in val and "salinity" in val
    assert "mae" in val["temperature"]
    assert "r2" in val["temperature"]
    assert val["temperature"]["rmse"] > 0

    print("\n\nALL ENDPOINT TESTS PASSED ✅")


if __name__ == "__main__":
    with TestClient(app) as client:
        main(client)
