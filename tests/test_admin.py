import json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.services.case_loader import get_case_loader
from backend.app.services.database import MatchDatabase, get_database
from tests.test_leaderboard import create_mock_session

client = TestClient(app)


@pytest.fixture
def clean_admin_db(tmp_path: Path):
    """Isolated SQLite database for admin test suite."""
    test_db = MatchDatabase(db_path=tmp_path / "admin_test.sqlite")
    app.dependency_overrides[get_database] = lambda: test_db
    yield test_db
    app.dependency_overrides.clear()


def test_admin_stats_empty(clean_admin_db: MatchDatabase):
    response = client.get("/api/admin/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["total_matches"] == 0
    assert data["average_score"] == 0.0
    assert data["highest_score"] == 0
    assert data["lowest_score"] == 0
    assert data["perfect_or_s_count"] == 0
    assert data["culprit_solved_count"] == 0
    assert data["culprit_solve_rate"] == 0.0
    assert data["most_popular_case"] == "None"


def test_admin_stats_with_data(clean_admin_db: MatchDatabase):
    loader = get_case_loader()
    case1 = loader.get_case("case_01_blackwood_manor")
    case2 = loader.get_case("case_02_neon_nexus")

    s1 = create_mock_session("relay_s1", "Team 1", case1, total_score=100, culprit_score=40)
    s2 = create_mock_session("relay_s2", "Team 2", case1, total_score=80, culprit_score=40)
    s3 = create_mock_session("relay_s3", "Team 3", case2, total_score=60, culprit_score=0)

    clean_admin_db.save_match(s1)
    clean_admin_db.save_match(s2)
    clean_admin_db.save_match(s3)

    response = client.get("/api/admin/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["total_matches"] == 3
    assert data["average_score"] == 80.0
    assert data["highest_score"] == 100
    assert data["lowest_score"] == 60
    assert data["perfect_or_s_count"] == 1
    assert data["culprit_solved_count"] == 2
    assert data["culprit_solve_rate"] == pytest.approx(66.7, 0.1)
    assert "Blackwood Manor" in data["most_popular_case"]


def test_admin_list_and_get_matches(clean_admin_db: MatchDatabase):
    loader = get_case_loader()
    case = loader.get_case("case_01_blackwood_manor")
    s = create_mock_session("relay_inspect_1", "SherlockTrio", case, total_score=95)
    clean_admin_db.save_match(s)

    # List matches
    list_res = client.get("/api/admin/matches")
    assert list_res.status_code == 200
    matches = list_res.json()
    assert len(matches) == 1
    assert matches[0]["session_id"] == "relay_inspect_1"
    assert matches[0]["team_name"] == "SherlockTrio"
    assert "user_1_prompt" in matches[0]
    assert "agent_1_output" in matches[0]

    # Get single match
    detail_res = client.get("/api/admin/matches/relay_inspect_1")
    assert detail_res.status_code == 200
    detail = detail_res.json()
    assert detail["session_id"] == "relay_inspect_1"
    assert detail["final_verdict"]["culprit"] == "Dr. Arthur Bell"
    assert detail["evaluation"]["total_score"] == 95

    # 404 for nonexistent match
    not_found_res = client.get("/api/admin/matches/nonexistent_123")
    assert not_found_res.status_code == 404


def test_admin_delete_single_match(clean_admin_db: MatchDatabase):
    loader = get_case_loader()
    case = loader.get_case("case_01_blackwood_manor")
    s1 = create_mock_session("relay_keep", "Keepers", case, total_score=80)
    s2 = create_mock_session("relay_delete", "Deleters", case, total_score=20)
    clean_admin_db.save_match(s1)
    clean_admin_db.save_match(s2)

    assert len(clean_admin_db.get_all_matches()) == 2

    # Delete s2
    del_res = client.delete("/api/admin/matches/relay_delete")
    assert del_res.status_code == 200
    assert "deleted successfully" in del_res.json()["message"]

    remaining = clean_admin_db.get_all_matches()
    assert len(remaining) == 1
    assert remaining[0]["session_id"] == "relay_keep"

    # Delete non-existent
    del_not_found = client.delete("/api/admin/matches/relay_nonexistent")
    assert del_not_found.status_code == 404


def test_admin_export_csv(clean_admin_db: MatchDatabase):
    loader = get_case_loader()
    case = loader.get_case("case_01_blackwood_manor")
    s = create_mock_session("relay_csv_1", "DataWizards", case, total_score=100)
    clean_admin_db.save_match(s)

    response = client.get("/api/admin/export/csv")
    assert response.status_code == 200
    assert "text/csv" in response.headers.get("content-type", "")
    assert "attachment; filename=\"prompt_relay_leaderboard.csv\"" in response.headers.get("content-disposition", "")
    csv_text = response.text
    assert "Rank,Team Name,Case ID,Case Title,Total Score" in csv_text
    assert "DataWizards" in csv_text
    assert "100" in csv_text


def test_admin_export_json(clean_admin_db: MatchDatabase):
    loader = get_case_loader()
    case = loader.get_case("case_01_blackwood_manor")
    s = create_mock_session("relay_json_1", "JsonJedi", case, total_score=90)
    clean_admin_db.save_match(s)

    response = client.get("/api/admin/export/json")
    assert response.status_code == 200
    assert "application/json" in response.headers.get("content-type", "")
    assert "attachment; filename=\"prompt_relay_tournament_archive.json\"" in response.headers.get("content-disposition", "")
    archive = response.json()
    assert isinstance(archive, list)
    assert len(archive) == 1
    assert archive[0]["team_name"] == "JsonJedi"
    assert archive[0]["total_score"] == 90
    assert "final_verdict" in archive[0]


def test_admin_cases_inspector():
    response = client.get("/api/admin/cases")
    assert response.status_code == 200
    cases = response.json()
    assert len(cases) >= 3
    for c in cases:
        assert "case_id" in c
        assert "title" in c
        assert "ground_truth" in c
        assert "leak_keywords" in c
        assert "culprit" in c["ground_truth"]


def test_admin_reset_tournament(clean_admin_db: MatchDatabase):
    loader = get_case_loader()
    case = loader.get_case("case_01_blackwood_manor")
    clean_admin_db.save_match(create_mock_session("relay_wipe", "WipeSquad", case))

    assert len(clean_admin_db.get_all_matches()) == 1

    res = client.post("/api/admin/reset")
    assert res.status_code == 200
    assert "reset successfully" in res.json()["message"]

    assert len(clean_admin_db.get_all_matches()) == 0


def test_admin_create_and_delete_custom_case():
    payload = {
        "case_id": "case_test_cyber_heist",
        "title": "The Quantum Vault Heist",
        "difficulty": "Hard",
        "synopsis": "A quantum cryptographer is found paralyzed inside an air-gapped vault.",
        "noisy_case_file": "Detailed story with multiple suspects, timestamps, and an EMP device clue.",
        "ground_truth": {
            "culprit": "Agent Sterling",
            "weapon_or_method": "Ultrasonic neuro-frequency transmitter",
            "key_clue": "Resonance frequency log on burner phone",
            "motive": "Espionage and stealing quantum encryption keys",
            "suspects": ["Agent Sterling", "Dr. Vance", "Maya Lin"],
        },
        "leak_keywords": ["Sterling", "ultrasonic", "neuro-frequency"],
    }

    # 1. Create custom case
    create_res = client.post("/api/admin/cases", json=payload)
    assert create_res.status_code == 201
    created_case = create_res.json()
    assert created_case["case_id"] == "case_test_cyber_heist"
    assert created_case["title"] == "The Quantum Vault Heist"

    # 2. Verify it shows up in cases list
    cases_res = client.get("/api/game/cases")
    assert cases_res.status_code == 200
    case_ids = [c["case_id"] for c in cases_res.json()]
    assert "case_test_cyber_heist" in case_ids

    # 3. Delete the custom case
    del_res = client.delete("/api/admin/cases/case_test_cyber_heist")
    assert del_res.status_code == 200
    assert "deleted successfully" in del_res.json()["message"]

    # 4. Verify it is gone
    cases_res_after = client.get("/api/game/cases")
    case_ids_after = [c["case_id"] for c in cases_res_after.json()]
    assert "case_test_cyber_heist" not in case_ids_after


def test_admin_delete_builtin_case_rejected():
    res = client.delete("/api/admin/cases/case_01_blackwood_manor")
    assert res.status_code == 400
    assert "cannot delete built-in case" in res.json()["detail"].lower()


def test_admin_llm_status_and_configuration():
    # 1. Configure to offline provider
    config_res = client.post(
        "/api/admin/llm/configure",
        json={
            "provider": "offline",
            "model_name": "offline-relay-simulator",
            "temperature": 0.0,
            "fallback_to_offline": True,
        },
    )
    assert config_res.status_code == 200
    data = config_res.json()
    assert data["provider"] == "offline"
    assert data["status"] == "connected"
    assert data["latency_ms"] is not None

    # 2. Check status endpoint
    status_res = client.get("/api/admin/llm/status")
    assert status_res.status_code == 200
    status_data = status_res.json()
    assert status_data["provider"] == "offline"
    assert status_data["fallback_to_offline"] is True


def test_mock_offline_chat_model_pipeline():
    from backend.app.core.llm import MockOfflineChatModel
    from backend.app.graph.nodes import agent_1_extractor, agent_2_reconstructor, agent_3_detective

    mock_llm = MockOfflineChatModel()

    # Step 1: Strong prompt for extraction
    state1 = {
        "user_1_prompt": "Extract all verified forensic clues, chemical residues, and suspect timestamped alibis while filtering out ambient noise and red herrings. Do not accuse anyone.",
        "case_file": "Victim was poisoned at Blackwood Manor.",
        "ground_truth": {"culprit": "Dr. Arthur Bell", "suspects": ["Dr. Arthur Bell", "Lady Beatrice"]},
        "leak_keywords": ["cyanide"],
    }
    res1 = agent_1_extractor(state1, llm=mock_llm)
    assert "Verified Clues" in res1["agent_1_output"]

    # Step 2: Strong prompt for reconstruction
    state2 = {
        "user_2_prompt": "Construct an objective minute-by-minute timeline tracking suspect movements and cross-referencing alibis against physical evidence to expose contradictions. Do not name the killer.",
        "agent_1_output": res1["agent_1_output"],
        "ground_truth": {"culprit": "Dr. Arthur Bell"},
        "leak_keywords": [],
    }
    res2 = agent_2_reconstructor(state2, llm=mock_llm)
    assert "Reconstructed Chronological Sequence" in res2["agent_2_output"]

    # Step 3: Strong prompt for deduction
    state3 = {
        "user_3_prompt": "Deduce the true culprit by disproving alibis with timeline contradictions, determine the exact weapon and delivery mechanism, and identify the smoking gun clue. Output strictly valid JSON with culprit, method, clue.",
        "agent_2_output": res2["agent_2_output"],
    }
    res3 = agent_3_detective(state3, llm=mock_llm)
    assert res3["final_verdict"]["culprit"] == "Dr. Arthur Bell"
    assert res3["_was_clean_json"] is True


def test_mock_offline_chat_model_weak_prompt_scaling():
    from backend.app.core.llm import MockOfflineChatModel
    from backend.app.graph.nodes import (
        agent_1_extractor,
        agent_2_reconstructor,
        agent_3_detective,
        agent_evaluator,
    )

    mock_llm = MockOfflineChatModel()

    # Step 1: Weak prompt yields minimal/incomplete extraction
    state1 = {
        "user_1_prompt": "Extract facts.",
        "case_file": "Victim was poisoned at Blackwood Manor.",
        "ground_truth": {"culprit": "Dr. Arthur Bell", "suspects": ["Dr. Arthur Bell", "Lady Beatrice"]},
        "leak_keywords": ["cyanide"],
    }
    res1 = agent_1_extractor(state1, llm=mock_llm)
    assert "[EXTRACTION INCOMPLETE" in res1["agent_1_output"]

    # Step 2: Weak prompt yields minimal/incomplete timeline
    state2 = {
        "user_2_prompt": "Make timeline.",
        "agent_1_output": res1["agent_1_output"],
        "ground_truth": {"culprit": "Dr. Arthur Bell"},
        "leak_keywords": [],
    }
    res2 = agent_2_reconstructor(state2, llm=mock_llm)
    assert "[TIMELINE INCOMPLETE" in res2["agent_2_output"]

    # Step 3: Weak prompt yields unfinished/undetermined verdict JSON
    state3 = {
        "user_3_prompt": "Who did it?",
        "agent_2_output": res2["agent_2_output"],
        "ground_truth": {
            "culprit": "Dr. Arthur Bell",
            "weapon_or_method": "Potassium cyanide coated onto sugar cubes using silver sugar tongs",
            "key_clue": "Muddy boots from greenhouse path",
            "suspects": ["Dr. Arthur Bell"],
        },
    }
    res3 = agent_3_detective(state3, llm=mock_llm)
    assert "Undetermined" in res3["final_verdict"]["culprit"]
    assert "Unspecified" in res3["final_verdict"]["method"]
    assert "Unspecified" in res3["final_verdict"]["clue"]

    # Evaluator scores the weak pipeline as 0 points (Unsolved F)
    state3["final_verdict"] = res3["final_verdict"]
    state3["_was_clean_json"] = res3["_was_clean_json"]
    eval_res = agent_evaluator(state3)
    assert eval_res["evaluation"]["total_score"] == 0
    assert eval_res["evaluation"]["grade"] == "Unsolved (F)"
    assert eval_res["evaluation"]["breakdown"]["culprit"]["status"] == "missing"
    assert eval_res["evaluation"]["breakdown"]["method"]["status"] == "missing"
    assert eval_res["evaluation"]["breakdown"]["clue"]["status"] == "missing"
    assert eval_res["evaluation"]["breakdown"]["format"]["status"] == "failed"

