import pytest
from backend.app.services.case_loader import CaseLoader, get_case_loader
from backend.app.models.case import CaseModel


@pytest.fixture
def case_loader():
    return CaseLoader()


def test_load_all_cases(case_loader):
    cases = case_loader.list_cases()
    assert len(cases) >= 3, f"Expected at least 3 cases, got {len(cases)}"
    
    case_ids = {c.case_id for c in cases}
    assert "case_01_blackwood_manor" in case_ids
    assert "case_02_neon_nexus" in case_ids
    assert "case_03_velvet_vault" in case_ids


def test_case_model_validation(case_loader):
    for case in case_loader.list_cases():
        assert isinstance(case, CaseModel)
        assert len(case.title) > 0
        assert len(case.synopsis) > 0
        assert len(case.noisy_case_file) > 200, f"Case {case.case_id} noisy_case_file too short"
        assert case.ground_truth.culprit in case.ground_truth.suspects
        assert len(case.ground_truth.weapon_or_method) > 0
        assert len(case.ground_truth.key_clue) > 0
        assert len(case.ground_truth.motive) > 0
        assert len(case.leak_keywords) >= 1
        assert len(case.decoy_clues) >= 1


def test_get_case_by_id(case_loader):
    case = case_loader.get_case("case_01_blackwood_manor")
    assert case is not None
    assert case.title == "The Poisoned Heir of Blackwood Manor"
    assert case.ground_truth.culprit == "Dr. Arthur Bell"

    # Non-existent ID returns None
    missing = case_loader.get_case("non_existent_case_xyz")
    assert missing is None


def test_get_random_case(case_loader):
    # Should return any valid case
    case = case_loader.get_random_case()
    assert isinstance(case, CaseModel)

    # Exclude two cases and ensure the third is chosen
    exclude = ["case_01_blackwood_manor", "case_02_neon_nexus"]
    picked = case_loader.get_random_case(exclude_ids=exclude)
    assert picked.case_id == "case_03_velvet_vault"


def test_check_leak_detection(case_loader):
    case = case_loader.get_case("case_01_blackwood_manor")
    assert case is not None

    # Safe text: no leaks
    safe_timeline = (
        "8:00 PM: Tea was served by the butler. 8:30 PM: Storm caused gas lamps to flicker. "
        "8:42 PM: Mantle clock was found stopped. 9:15 PM: Lord Reginald was found unresponsive."
    )
    is_leaked, matches = case_loader.check_leak(case, safe_timeline)
    assert not is_leaked
    assert matches == []

    # Leaking text mentioning culprit's name
    leaked_text_1 = "The timeline indicates Dr. Arthur Bell must have slipped something in the cup."
    is_leaked, matches = case_loader.check_leak(case, leaked_text_1)
    assert is_leaked
    assert any("Bell" in m for m in matches)

    # Leaking text with lower-case keyword
    leaked_text_2 = "8:35 PM: footsteps heard. 9:05 PM: dr. bell arrived with muddy boots."
    is_leaked, matches = case_loader.check_leak(case, leaked_text_2)
    assert is_leaked
    assert any("Bell" in m for m in matches)
