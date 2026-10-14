import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.models.case import CaseModel, GroundTruth
from backend.app.services.case_loader import get_case_loader
from backend.app.services.database import MatchDatabase, get_database
from backend.app.services.session_manager import GameSession, get_session_manager

client = TestClient(app)


def create_mock_session(
    session_id: str,
    team_name: str,
    case: CaseModel,
    total_score: int = 100,
    grade: str = "Master Detective (S)",
    culprit_score: int = 40,
    method_score: int = 25,
    clue_score: int = 20,
    format_score: int = 15,
) -> GameSession:
    """Helper to construct a mock completed GameSession."""
    return GameSession(
        session_id=session_id,
        team_name=team_name,
        case=case,
        current_step="completed",
        state={
            "session_id": session_id,
            "team_name": team_name,
            "case_id": case.case_id,
            "case_file": case.noisy_case_file,
            "ground_truth": case.ground_truth.model_dump(),
            "leak_keywords": case.leak_keywords,
            "user_1_prompt": "Extract facts without spoilers.",
            "agent_1_output": "Extracted facts: Earl Grey tea, 8:00 PM.",
            "user_2_prompt": "Synthesize timeline without naming culprit.",
            "agent_2_output": "Timeline synthesized.",
            "user_3_prompt": "Who is the killer? Return JSON.",
            "raw_agent_3_output": '{"culprit": "Dr. Arthur Bell"}',
            "final_verdict": {
                "culprit": "Dr. Arthur Bell",
                "method": "Potassium cyanide in sugar cubes",
                "clue": "Muddy boots from greenhouse path",
            },
            "evaluation": {
                "total_score": total_score,
                "grade": grade,
                "breakdown": {
                    "culprit": {"points": culprit_score, "max": 40, "status": "correct"},
                    "method": {"points": method_score, "max": 25, "status": "correct"},
                    "clue": {"points": clue_score, "max": 20, "status": "correct"},
                    "format": {"points": format_score, "max": 15, "status": "correct"},
                },
                "feedback": ["Flawless investigative relay."],
            },
        },
        created_at="2026-09-24T10:00:00+00:00",
        updated_at="2026-09-24T10:15:00+00:00",
    )


# ==============================================================================
# Database Unit Tests
# ==============================================================================

def test_database_initialization(tmp_path: Path):
    db_file = tmp_path / "test_init.sqlite"
    db = MatchDatabase(db_path=db_file)
    assert db_file.exists()
    assert db.get_leaderboard() == []


def test_save_and_retrieve_match(tmp_path: Path):
    db_file = tmp_path / "test_match.sqlite"
    db = MatchDatabase(db_path=db_file)
    loader = get_case_loader()
    case = loader.get_case("case_01_blackwood_manor")

    session = create_mock_session("relay_001", "SherlockSquad", case, total_score=95, grade="Master Detective (S)")
    db.save_match(session, completed_at="2026-09-24T12:00:00+00:00")

    match = db.get_match("relay_001")
    assert match is not None
    assert match["session_id"] == "relay_001"
    assert match["team_name"] == "SherlockSquad"
    assert match["case_id"] == "case_01_blackwood_manor"
    assert match["total_score"] == 95
    assert match["grade"] == "Master Detective (S)"
    assert match["culprit_score"] == 40
    assert match["method_score"] == 25
    assert match["clue_score"] == 20
    assert match["format_score"] == 15
    assert match["final_verdict"]["culprit"] == "Dr. Arthur Bell"
    assert match["evaluation"]["total_score"] == 95
    assert match["user_1_prompt"] == "Extract facts without spoilers."
    assert match["agent_1_output"] == "Extracted facts: Earl Grey tea, 8:00 PM."


def test_get_match_not_found(tmp_path: Path):
    db_file = tmp_path / "test_not_found.sqlite"
    db = MatchDatabase(db_path=db_file)
    assert db.get_match("nonexistent_session") is None


def test_leaderboard_ranking_and_tie_breaking(tmp_path: Path):
    db_file = tmp_path / "test_ranking.sqlite"
    db = MatchDatabase(db_path=db_file)
    loader = get_case_loader()
    case = loader.get_case("case_01_blackwood_manor")

    # Team Alpha: 100 points, completed at 10:00
    s_alpha = create_mock_session("relay_alpha", "Team Alpha", case, total_score=100)
    db.save_match(s_alpha, completed_at="2026-09-24T10:00:00+00:00")

    # Team Beta: 100 points, completed at 10:05 (tied score, completed later -> rank 2)
    s_beta = create_mock_session("relay_beta", "Team Beta", case, total_score=100)
    db.save_match(s_beta, completed_at="2026-09-24T10:05:00+00:00")

    # Team Gamma: 85 points, completed at 09:30 -> rank 3
    s_gamma = create_mock_session("relay_gamma", "Team Gamma", case, total_score=85, grade="Lead Investigator (A)")
    db.save_match(s_gamma, completed_at="2026-09-24T09:30:00+00:00")

    # Team Delta: 40 points, completed at 11:00 -> rank 4
    s_delta = create_mock_session("relay_delta", "Team Delta", case, total_score=40, grade="Apprentice Sleuth (C)")
    db.save_match(s_delta, completed_at="2026-09-24T11:00:00+00:00")

    leaderboard = db.get_leaderboard()
    assert len(leaderboard) == 4

    assert leaderboard[0]["rank"] == 1
    assert leaderboard[0]["team_name"] == "Team Alpha"
    assert leaderboard[0]["total_score"] == 100

    assert leaderboard[1]["rank"] == 2
    assert leaderboard[1]["team_name"] == "Team Beta"
    assert leaderboard[1]["total_score"] == 100

    assert leaderboard[2]["rank"] == 3
    assert leaderboard[2]["team_name"] == "Team Gamma"
    assert leaderboard[2]["total_score"] == 85

    assert leaderboard[3]["rank"] == 4
    assert leaderboard[3]["team_name"] == "Team Delta"
    assert leaderboard[3]["total_score"] == 40


def test_leaderboard_limit(tmp_path: Path):
    db_file = tmp_path / "test_limit.sqlite"
    db = MatchDatabase(db_path=db_file)
    loader = get_case_loader()
    case = loader.get_case("case_01_blackwood_manor")

    for i in range(5):
        s = create_mock_session(f"relay_{i}", f"Team {i}", case, total_score=50 + i * 10)
        db.save_match(s)

    top_2 = db.get_leaderboard(limit=2)
    assert len(top_2) == 2
    assert top_2[0]["rank"] == 1
    assert top_2[0]["total_score"] == 90
    assert top_2[1]["rank"] == 2
    assert top_2[1]["total_score"] == 80


def test_upsert_existing_session(tmp_path: Path):
    db_file = tmp_path / "test_upsert.sqlite"
    db = MatchDatabase(db_path=db_file)
    loader = get_case_loader()
    case = loader.get_case("case_01_blackwood_manor")

    session = create_mock_session("relay_upsert", "OriginalTeam", case, total_score=60)
    db.save_match(session)
    assert db.get_match("relay_upsert")["total_score"] == 60

    # Modify and re-save with same session_id
    session.state["evaluation"]["total_score"] = 85
    db.save_match(session)

    leaderboard = db.get_leaderboard()
    assert len(leaderboard) == 1
    assert leaderboard[0]["total_score"] == 85


def test_clear_database(tmp_path: Path):
    db_file = tmp_path / "test_clear.sqlite"
    db = MatchDatabase(db_path=db_file)
    loader = get_case_loader()
    case = loader.get_case("case_01_blackwood_manor")

    db.save_match(create_mock_session("relay_001", "Team 1", case))
    assert len(db.get_leaderboard()) == 1

    db.clear()
    assert len(db.get_leaderboard()) == 0


# ==============================================================================
# API Endpoint Integration Tests
# ==============================================================================

@pytest.fixture
def clean_db(tmp_path: Path):
    """Use an isolated SQLite database for API tests."""
    test_db = MatchDatabase(db_path=tmp_path / "api_test.sqlite")
    # Override get_database dependency in app
    app.dependency_overrides[get_database] = lambda: test_db
    yield test_db
    app.dependency_overrides.clear()


def test_api_empty_leaderboard(clean_db: MatchDatabase):
    response = client.get("/api/game/leaderboard")
    assert response.status_code == 200
    data = response.json()
    assert data["total_matches"] == 0
    assert data["leaderboard"] == []


def test_api_leaderboard_with_records(clean_db: MatchDatabase):
    loader = get_case_loader()
    case = loader.get_case("case_01_blackwood_manor")

    s1 = create_mock_session("relay_api_1", "BinaryBakers", case, total_score=90, grade="Lead Investigator (A)")
    s2 = create_mock_session("relay_api_2", "QuantumQuirks", case, total_score=100, grade="Master Detective (S)")
    clean_db.save_match(s1, completed_at="2026-09-24T12:00:00+00:00")
    clean_db.save_match(s2, completed_at="2026-09-24T12:05:00+00:00")

    response = client.get("/api/game/leaderboard")
    assert response.status_code == 200
    data = response.json()
    assert data["total_matches"] == 2
    assert len(data["leaderboard"]) == 2

    # QuantumQuirks should be #1 with 100 points
    assert data["leaderboard"][0]["rank"] == 1
    assert data["leaderboard"][0]["team_name"] == "QuantumQuirks"
    assert data["leaderboard"][0]["total_score"] == 100

    # BinaryBakers should be #2 with 90 points
    assert data["leaderboard"][1]["rank"] == 2
    assert data["leaderboard"][1]["team_name"] == "BinaryBakers"
    assert data["leaderboard"][1]["total_score"] == 90


def test_api_delete_leaderboard(clean_db: MatchDatabase):
    loader = get_case_loader()
    case = loader.get_case("case_01_blackwood_manor")
    clean_db.save_match(create_mock_session("relay_to_delete", "DoomedTeam", case))

    assert len(clean_db.get_leaderboard()) == 1

    delete_resp = client.delete("/api/game/leaderboard")
    assert delete_resp.status_code == 200
    assert "reset successfully" in delete_resp.json()["message"]

    get_resp = client.get("/api/game/leaderboard")
    assert get_resp.status_code == 200
    assert get_resp.json()["total_matches"] == 0
    assert get_resp.json()["leaderboard"] == []


from unittest.mock import patch

@patch("backend.app.api.game.agent_1_extractor")
@patch("backend.app.api.game.agent_2_reconstructor")
@patch("backend.app.api.game.agent_3_detective")
def test_api_match_completion_persists_to_leaderboard(
    mock_step3, mock_step2, mock_step1, clean_db: MatchDatabase
):
    mock_step1.return_value = {"agent_1_output": "Key clues found."}
    mock_step2.return_value = {
        "agent_2_output": "Clean timeline without spoilers.",
        "leak_detected": False,
        "leak_keywords_found": [],
    }
    mock_step3.return_value = {
        "raw_agent_3_output": '{"culprit": "Dr. Arthur Bell", "method": "Cyanide", "clue": "Muddy boots"}',
        "final_verdict": {
            "culprit": "Dr. Arthur Bell",
            "method": "Potassium cyanide in sugar cubes using silver sugar tongs",
            "clue": "Muddy boots from greenhouse path and cyanide on tongs",
        },
        "_was_clean_json": True,
    }

    # 1. Start game
    start = client.post("/api/game/start", json={"team_name": "RelayRoyals", "case_id": "case_01_blackwood_manor"})
    assert start.status_code == 200
    sess_id = start.json()["session_id"]

    # 2. Step 1
    s1 = client.post(
        "/api/game/step1",
        json={
            "session_id": sess_id,
            "user_1_prompt": "Role: Evidence Extractor. Identify key people, times, locations, and movements. Distinguish confirmed facts from uncertain information and filter irrelevant noise. Do not infer causes or actions.",
        },
    )
    assert s1.status_code == 200

    # 3. Step 2
    s2 = client.post(
        "/api/game/step2",
        json={
            "session_id": sess_id,
            "user_2_prompt": "Role: Incident Reconstructor. Organize events in chronological sequence of what happened first and next. Connect relevant people, locations, and movements. Identify key dependencies while keeping uncertain relations separate.",
        },
    )
    assert s2.status_code == 200

    # 4. Step 3 (Persists match)
    s3 = client.post(
        "/api/game/step3",
        json={
            "session_id": sess_id,
            "user_3_prompt": "Role: Decision Solver. Analyze the reconstructed timeline and operational rules to determine the valid operational action. Identify supporting rules, blocking condition, and resume condition. Output strict JSON with keys: culprit, method, clue.",
        },
    )
    assert s3.status_code == 200
    assert s3.json()["total_score"] == 100

    # 5. Query leaderboard
    lb_resp = client.get("/api/game/leaderboard")
    assert lb_resp.status_code == 200
    lb_data = lb_resp.json()
    assert lb_data["total_matches"] == 1
    assert lb_data["leaderboard"][0]["team_name"] == "RelayRoyals"
    assert lb_data["leaderboard"][0]["total_score"] == 100
    assert lb_data["leaderboard"][0]["rank"] == 1

