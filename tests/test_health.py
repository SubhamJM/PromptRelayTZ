from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert data["health"] == "/api/health"


def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "Prompt Relay"
    assert "llm" in data
    assert data["llm"]["default_provider"] == "gemini"
    assert data["llm"]["default_model"] == "gemini-3.5-flash-lite"
    assert "has_gemini_key" in data["llm"]
