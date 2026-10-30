from unittest.mock import patch
import pytest
from fastapi.testclient import TestClient
from langchain_core.language_models.fake_chat_models import FakeListChatModel

from backend.app.main import app
from backend.app.services.session_manager import get_session_manager

client = TestClient(app)


from backend.app.services.database import MatchDatabase, get_database


@pytest.fixture(autouse=True)
def clean_environment(tmp_path):
    """Clear in-memory sessions and use isolated SQLite database for tests."""
    manager = get_session_manager()
    manager.clear()
    test_db = MatchDatabase(db_path=tmp_path / "test_api_matches.sqlite")
    app.dependency_overrides[get_database] = lambda: test_db
    yield
    app.dependency_overrides.clear()


def test_list_cases():
    response = client.get("/api/game/cases")
    assert response.status_code == 200
    cases = response.json()
    assert len(cases) == 2

    case_ids = {c["case_id"] for c in cases}
    assert "case_04_airport_crisis" in case_ids
    assert "case_05_museum_heist" in case_ids

    # Ensure secrets are not leaked
    first_case = cases[0]
    assert "case_id" in first_case
    assert "title" in first_case
    assert "synopsis" in first_case
    assert "difficulty" in first_case
    assert "ground_truth" not in first_case
    assert "leak_keywords" not in first_case


def test_start_game_specific_case():
    payload = {
        "team_name": "CyberDetectives",
        "case_id": "case_04_airport_crisis",
    }
    response = client.post("/api/game/start", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["session_id"].startswith("relay_")
    assert data["team_name"] == "CyberDetectives"
    assert data["case_id"] == "case_04_airport_crisis"
    assert "Airport Crisis" in data["case_title"]
    assert len(data["case_file"]) > 100


def test_start_game_museum_heist():
    payload = {
        "team_name": "LouvreGuardians",
        "scenario_id": "scenario_05_museum_heist",
    }
    response = client.post("/api/game/start", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["team_name"] == "LouvreGuardians"
    assert data["case_id"] == "case_05_museum_heist"
    assert "Riverton Museum" in data["case_title"]
    assert len(data["images"]) == 10
    assert len(data["operational_rules"]) == 3


def test_start_game_random_case():
    payload = {"team_name": "RandomTeam"}
    response = client.post("/api/game/start", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    assert data["team_name"] == "RandomTeam"
    assert data["case_id"] in [
        "case_04_airport_crisis",
        "case_05_museum_heist",
    ]


def test_start_game_invalid_case():
    payload = {"team_name": "BadCaseTeam", "case_id": "non_existent_case_999"}
    response = client.post("/api/game/start", json=payload)
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


@patch("backend.app.api.game.agent_1_extractor")
@patch("backend.app.api.game.agent_2_reconstructor")
@patch("backend.app.api.game.agent_3_detective")
def test_full_wizard_progression(mock_step3, mock_step2, mock_step1):
    # Mock node returns
    mock_step1.return_value = {"agent_1_output": "Extracted facts: Lord Reginald died with Earl Grey tea."}
    mock_step2.return_value = {
        "agent_2_output": "Timeline: 8:00 PM tea served. 9:15 PM body found.",
        "leak_detected": False,
        "leak_keywords_found": [],
    }
    mock_step3.return_value = {
        "raw_agent_3_output": '{"culprit": "Hold Flight SW 472 at Gate B07 and dispatch K9 unit to inspect unattended blue suitcase", "method": "Rule SEC-101 (Unattended Baggage Protocol) and Rule OPS-204 (Pre-Departure Security Hold)", "clue": "Unattended blue suitcase at Gate B07 window seats with Daniel Kim bag tag awaiting K9 explosive clearance"}',
        "final_verdict": {
            "culprit": "Hold Flight SW 472 at Gate B07 and dispatch K9 unit to inspect unattended blue suitcase",
            "method": "Rule SEC-101 (Unattended Baggage Protocol) and Rule OPS-204 (Pre-Departure Security Hold)",
            "clue": "Unattended blue suitcase at Gate B07 window seats with Daniel Kim bag tag awaiting K9 explosive clearance",
        },
        "_was_clean_json": True,
    }

    # 1. Start session
    start_resp = client.post(
        "/api/game/start",
        json={"team_name": "VictoryVanguard", "case_id": "case_04_airport_crisis"},
    )
    assert start_resp.status_code == 200
    session_id = start_resp.json()["session_id"]

    # 2. Step 1 (Player 1)
    step1_resp = client.post(
        "/api/game/step1",
        json={
            "session_id": session_id,
            "user_1_prompt": "Role: Evidence Extractor. Identify key people, times, locations, and movements. Distinguish confirmed facts from uncertain information and filter irrelevant noise. Do not infer causes or actions.",
        },
    )
    assert step1_resp.status_code == 200
    assert "Extracted facts" in step1_resp.json()["agent_1_output"]

    # 3. Step 2 (Player 2)
    step2_resp = client.post(
        "/api/game/step2",
        json={
            "session_id": session_id,
            "user_2_prompt": "Role: Incident Reconstructor. Organize events in chronological sequence of what happened first and next. Connect relevant people, locations, and movements. Identify key dependencies while keeping uncertain relations separate.",
        },
    )
    assert step2_resp.status_code == 200
    assert "Timeline:" in step2_resp.json()["agent_2_output"]
    assert step2_resp.json()["leak_detected"] is False

    # 4. Step 3 (Player 3)
    step3_resp = client.post(
        "/api/game/step3",
        json={
            "session_id": session_id,
            "user_3_prompt": "Role: Decision Solver. Analyze the reconstructed timeline and operational rules to determine the valid operational action. Identify supporting rules, blocking condition, and resume condition. Output strict JSON with keys: culprit, method, clue.",
        },
    )
    assert step3_resp.status_code == 200
    step3_data = step3_resp.json()
    assert step3_data["total_score"] == 100
    assert step3_data["grade"] == "Master Detective (S)"
    assert "Flight SW 472" in step3_data["final_verdict"]["culprit"]
    assert step3_data["evaluation"]["breakdown"]["culprit"]["status"] == "correct"

    # 5. Get Session Status
    status_resp = client.get(f"/api/game/session/{session_id}")
    assert status_resp.status_code == 200
    status_data = status_resp.json()
    assert status_data["current_step"] == "completed"
    assert status_data["total_score"] == 100
    assert status_data["team_name"] == "VictoryVanguard"


def test_out_of_order_step_rejected():
    # Start session
    start_resp = client.post(
        "/api/game/start",
        json={"team_name": "RuleBreakers", "case_id": "case_04_airport_crisis"},
    )
    session_id = start_resp.json()["session_id"]

    # Attempt to jump straight to step 2
    step2_resp = client.post(
        "/api/game/step2",
        json={"session_id": session_id, "user_2_prompt": "Skipping ahead!"},
    )
    assert step2_resp.status_code == 400
    assert "invalid step progression" in step2_resp.json()["detail"].lower()

    # Attempt to jump straight to step 3
    step3_resp = client.post(
        "/api/game/step3",
        json={"session_id": session_id, "user_3_prompt": "Skipping to the end!"},
    )
    assert step3_resp.status_code == 400
    assert "invalid step progression" in step3_resp.json()["detail"].lower()


def test_session_not_found():
    response = client.get("/api/game/session/relay_fake_session_123")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_airport_crisis_relay_progression():
    # 1. Start Game with Airport Crisis case
    start_resp = client.post(
        "/api/game/start",
        json={"team_name": "CrisisCommandos", "case_id": "case_04_airport_crisis"},
    )
    assert start_resp.status_code == 200
    start_data = start_resp.json()
    assert start_data["case_id"] == "case_04_airport_crisis"
    assert start_data["theme"] == "Airport Crisis"
    assert len(start_data["images"]) == 10
    assert len(start_data["operational_rules"]) == 3
    session_id = start_data["session_id"]

    # 2. Step 1: User 1 Prompt for Vision/OCR Extractor
    step1_resp = client.post(
        "/api/game/step1",
        json={
            "session_id": session_id,
            "user_1_prompt": "Extract all verified timestamps, gate locations, baggage tags, and passenger movements. Distinguish confirmed observations from uncertain ones and ignore irrelevant marathon news.",
        },
    )
    assert step1_resp.status_code == 200
    step1_data = step1_resp.json()
    assert "agent_1_output" in step1_data
    assert len(step1_data["agent_1_output"]) > 50

    # 3. Step 2: User 2 Prompt for NetworkX Reconstructor
    step2_resp = client.post(
        "/api/game/step2",
        json={
            "session_id": session_id,
            "user_2_prompt": "Reconstruct the chronological timeline of events at Gate B07 minute by minute and connect passenger movements to the discovered unattended bag. Do not make a final operational action.",
        },
    )
    assert step2_resp.status_code == 200
    step2_data = step2_resp.json()
    assert "agent_2_output" in step2_data
    assert step2_data["leak_detected"] is False

    # 4. Step 3: User 3 Prompt for Z3 Solver Detective
    step3_resp = client.post(
        "/api/game/step3",
        json={
            "session_id": session_id,
            "user_3_prompt": "Evaluate the reconstructed sequence against airport operational rules and determine the required operational action, supporting rules, and blocking condition. Output strictly valid JSON with culprit, method, clue.",
        },
    )
    assert step3_resp.status_code == 200
    step3_data = step3_resp.json()
    assert "final_verdict" in step3_data
    assert "evaluation" in step3_data
    eval_res = step3_data["evaluation"]
    assert eval_res["total_score"] > 50
    assert "breakdown" in eval_res
    # Assert scorecards and prompt records
    assert "p1_scorecard" in eval_res
    assert eval_res["p1_scorecard"]["score"] > 0
    assert eval_res["p1_scorecard"]["itemized_feedback"] != ""
    assert "p2_scorecard" in eval_res
    assert eval_res["p2_scorecard"]["score"] > 0
    assert "p3_scorecard" in eval_res
    assert eval_res["p3_scorecard"]["score"] > 0
    assert "solution_scorecard" in eval_res
    assert "score" in eval_res["solution_scorecard"]

    # Assert Step3Response contains prompts and outputs
    assert step3_data.get("p1_prompt") is not None
    assert step3_data.get("a1_output") is not None
    assert step3_data.get("p2_prompt") is not None
    assert step3_data.get("a2_output") is not None
    assert step3_data.get("p3_prompt") is not None


def test_prompt_length_limits_enforced():
    start_resp = client.post(
        "/api/game/start",
        json={"team_name": "LengthTestTeam", "case_id": "case_04_airport_crisis"},
    )
    assert start_resp.status_code == 200
    session_id = start_resp.json()["session_id"]
    limits = start_resp.json().get("prompt_limits", {})
    assert limits.get("p1", {}).get("max_words") == 80
    assert limits.get("p2", {}).get("max_words") == 80
    assert limits.get("p3", {}).get("max_words") == 120

    # 1. Step 1: Prompt exceeding 80 words
    overlong_p1 = "word " * 85
    p1_fail_resp = client.post(
        "/api/game/step1",
        json={"session_id": session_id, "prompt": overlong_p1},
    )
    assert p1_fail_resp.status_code == 400
    assert "exceeds the limit of 80 words" in p1_fail_resp.json()["detail"]

    # Valid P1 prompt succeeds
    p1_ok_resp = client.post(
        "/api/game/step1",
        json={"session_id": session_id, "prompt": "Extract all verified clues and alibis without noise."},
    )
    assert p1_ok_resp.status_code == 200

    # 2. Step 2: Prompt exceeding 80 words
    overlong_p2 = "sequence " * 85
    p2_fail_resp = client.post(
        "/api/game/step2",
        json={"session_id": session_id, "prompt": overlong_p2},
    )
    assert p2_fail_resp.status_code == 400
    assert "exceeds the limit of 80 words" in p2_fail_resp.json()["detail"]

    # Valid P2 prompt succeeds
    p2_ok_resp = client.post(
        "/api/game/step2",
        json={"session_id": session_id, "prompt": "Reconstruct the timeline in chronological order."},
    )
    assert p2_ok_resp.status_code == 200

    # 3. Step 3: Prompt exceeding 120 words
    overlong_p3 = "verdict " * 125
    p3_fail_resp = client.post(
        "/api/game/step3",
        json={"session_id": session_id, "prompt": overlong_p3},
    )
    assert p3_fail_resp.status_code == 400
    assert "exceeds the limit of 120 words" in p3_fail_resp.json()["detail"]


def test_step1_after_server_restart_cache_clear():
    """Verify that sessions recovered from SQLite persistence after cache flush / restart don't crash on Step 1."""
    manager = get_session_manager()
    start_resp = client.post(
        "/api/game/start",
        json={"team_name": "CrashRecoveryTeam", "case_id": "case_04_airport_crisis"},
    )
    assert start_resp.status_code == 200
    session_id = start_resp.json()["session_id"]

    # Simulate server restart / memory cache flush so session is fetched from SQLite
    manager._cache.clear()

    # Step 1 submission must not raise AttributeError: 'dict' object has no attribute 'dossier_text'
    p1_resp = client.post(
        "/api/game/step1",
        json={"session_id": session_id, "prompt": "Extract all evidence from Gate B07 and check-in island."},
    )
    assert p1_resp.status_code == 200
    assert "a1_output" in p1_resp.json()

    # Flush again before step 2
    manager._cache.clear()
    p2_resp = client.post(
        "/api/game/step2",
        json={"session_id": session_id, "prompt": "Reconstruct timestamps from check-in to gate discovery."},
    )
    assert p2_resp.status_code == 200
    assert "a2_output" in p2_resp.json()

    # Flush again before step 3
    manager._cache.clear()
    p3_resp = client.post(
        "/api/game/step3",
        json={"session_id": session_id, "prompt": "Determine culprit and operational action for SW 472."},
    )
    assert p3_resp.status_code == 200
    assert "final_verdict" in p3_resp.json()
    assert "evaluation" in p3_resp.json()


