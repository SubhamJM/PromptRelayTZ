import pytest
from backend.app.services.case_loader import CaseLoader, get_case_loader
from backend.app.models.case import CaseModel


@pytest.fixture
def case_loader():
    return CaseLoader()


def test_load_all_cases(case_loader):
    cases = case_loader.list_cases()
    assert len(cases) == 2, f"Expected 2 image-based cases, got {len(cases)}"
    
    case_ids = {c.case_id for c in cases}
    assert "case_04_airport_crisis" in case_ids
    assert "case_05_museum_heist" in case_ids


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
    case = case_loader.get_case("case_04_airport_crisis")
    assert case is not None
    assert case.title == "Airport Crisis: Flight 472 Emergency"
    assert "Hold Flight SW 472" in case.ground_truth.culprit

    museum_case = case_loader.get_case("case_05_museum_heist")
    assert museum_case is not None
    assert museum_case.title == "The Riverton Museum Heist: The Celestial Madonna"
    assert museum_case.ground_truth.culprit == "Dr. Julian Vance"

    # Non-existent ID returns None
    missing = case_loader.get_case("non_existent_case_xyz")
    assert missing is None


def test_get_random_case(case_loader):
    # Should return any valid case
    case = case_loader.get_random_case()
    assert isinstance(case, CaseModel)

    # Exclude airport crisis and ensure museum heist is chosen
    exclude = ["case_04_airport_crisis"]
    picked = case_loader.get_random_case(exclude_ids=exclude)
    assert picked.case_id == "case_05_museum_heist"


def test_check_leak_detection(case_loader):
    case = case_loader.get_case("case_04_airport_crisis")
    assert case is not None

    # Safe text: no leaks
    safe_timeline = (
        "08:14 AM: Passenger checked in. 08:30 AM: Flight display shows boarding status. "
        "08:46 AM: Chatter regarding a blue suitcase near Gate B07. 08:49 AM: Security officer posted."
    )
    is_leaked, matches = case_loader.check_leak(case, safe_timeline)
    assert not is_leaked
    assert matches == []

    # Leaking text mentioning action keyword
    leaked_text_1 = "The supervisor ordered to Hold Flight SW 472 at Gate B07 immediately."
    is_leaked, matches = case_loader.check_leak(case, leaked_text_1)
    assert is_leaked
    assert any("Hold Flight SW 472" in m for m in matches)

    # Leaking text with rule keyword
    leaked_text_2 = "08:49 AM: Security officer invoked Rule SEC-101 for unattended luggage."
    is_leaked, matches = case_loader.check_leak(case, leaked_text_2)
    assert is_leaked
    assert any("SEC-101" in m for m in matches)


def test_airport_crisis_case_details(case_loader):
    case = case_loader.get_case("case_04_airport_crisis")
    assert case is not None
    assert case.theme == "Airport Crisis"
    assert "Flight 472" in case.title
    assert len(case.images) == 10
    
    first_img = case.images[0]
    assert first_img["filename"] == "1.png"
    assert first_img["src"] == "/image_data/1.png"
    assert len(case.operational_rules) == 3
    assert any("SEC-101" in r for r in case.operational_rules)
    assert any("OPS-204" in r for r in case.operational_rules)
    
    # Check operational ground truth fields
    gt = case.ground_truth
    assert gt.valid_action is not None
    assert "Hold Flight SW 472" in gt.valid_action
    assert len(gt.supporting_rules) >= 2
    assert gt.blocking_condition is not None
    assert gt.resume_condition is not None


def test_museum_heist_case_details(case_loader):
    case = case_loader.get_case("case_05_museum_heist")
    assert case is not None
    assert case.theme == "Art Heist & Forgery"
    assert "Celestial Madonna" in case.title
    assert len(case.images) == 10

    first_img = case.images[0]
    assert first_img["filename"] == "01_cctv_gallery.png"
    assert first_img["src"] == "/images_for_museum/01_cctv_gallery.png"
    assert len(case.operational_rules) == 3
    assert any("SEC-401" in r for r in case.operational_rules)
    assert any("ART-302" in r for r in case.operational_rules)

    gt = case.ground_truth
    assert gt.culprit == "Dr. Julian Vance"
    assert "Breaker B-04" in gt.weapon_or_method
    assert "CONSV-408" in gt.key_clue


def test_airport_crisis_static_images_served():
    from fastapi.testclient import TestClient
    from backend.app.main import app

    client = TestClient(app)
    res = client.get("/image_data/1.png")
    assert res.status_code == 200
    assert "image/png" in res.headers.get("content-type", "")
    assert len(res.content) > 1000


def test_vision_ocr_tool_with_image_attachments(case_loader):
    from backend.app.tools.vision_ocr import VisionOCREvidenceTool

    case = case_loader.get_case("case_04_airport_crisis")
    assert case is not None

    tool = VisionOCREvidenceTool()
    report = tool.run(case.noisy_case_file, images=case.images)
    
    assert "=== OCR & VISION TOOL EXTRACTION REPORT ===" in report
    assert "Visual Image Files Processed (10):" in report
    assert "1.png" in report
    assert "08:14:23" in report
