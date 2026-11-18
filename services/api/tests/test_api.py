from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health():
    assert client.get("/health/live").json() == {"status": "alive"}
    assert client.get("/health/ready").status_code == 200


def test_overview():
    response = client.get("/api/v1/overview?cases=8&seed=3")
    assert response.status_code == 200
    body = response.json()
    assert body["metrics"]["case_count"] == 8


def test_run():
    response = client.post("/api/v1/runs", json={"cases": 5, "seed": 11})
    assert response.status_code == 200
    assert response.json()["status"] == "completed"


def test_invalid_case_count():
    assert client.get("/api/v1/overview?cases=0").status_code == 422
