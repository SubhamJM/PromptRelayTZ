from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_station_ui_endpoint():
    response = client.get("/station")
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")
    assert "PROMPT RELAY" in response.text
    assert "Player 1: Evidence Extractor" in response.text
    assert "Player 2: Timeline Reconstructor" in response.text
    assert "Player 3: Final Detective" in response.text
    assert "modal-leaderboard" in response.text
    assert "Tournament Leaderboard" in response.text
    assert "modal-admin" in response.text
    assert "Organizer Control Center" in response.text
    assert "relay-chain-container" in response.text
    assert "Relay Chain Breakdown" in response.text
    assert "Tactical Strategy Tip: Evidence Filtering" in response.text
    assert "Tactical Strategy Tip: Timeline Reconstruction" in response.text
    assert "Tactical Strategy Tip: Final Detective" in response.text
    assert "admin-tab-btn-llm" in response.text
    assert "admin-tab-btn-cases" in response.text
    assert "admin-case-creator-form" in response.text


def test_app_alias_endpoint():
    response = client.get("/app")
    assert response.status_code == 200
    assert "PROMPT RELAY" in response.text


def test_static_assets_served():
    # CSS
    css_res = client.get("/assets/style.css")
    assert css_res.status_code == 200
    assert "animate-fade-in" in css_res.text

    # JS
    js_res = client.get("/assets/app.js")
    assert js_res.status_code == 200
    assert "handleStartGame" in js_res.text


def test_root_browser_vs_api_negotiation():
    # Browser Request (HTML)
    browser_res = client.get(
        "/",
        headers={"accept": "text/html,application/xhtml+xml", "user-agent": "Mozilla/5.0"},
    )
    assert browser_res.status_code == 200
    assert "PROMPT RELAY" in browser_res.text

    # API / TestClient Request (JSON)
    api_res = client.get("/")
    assert api_res.status_code == 200
    data = api_res.json()
    assert "message" in data
    assert data["health"] == "/api/health"
