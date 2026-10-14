import pytest
from backend.app.tools.vision_ocr import VisionOCREvidenceTool
from backend.app.tools.networkx_graph import NetworkXDependencyTool
from backend.app.tools.z3_solver import Z3ConstraintSolverTool
from backend.app.graph.evaluator import (
    evaluate_verdict,
    evaluate_player_1_prompt,
    evaluate_player_2_prompt,
    evaluate_player_3_prompt,
)
from backend.app.core.llm import classify_prompt_tier
from backend.app.services.case_loader import get_case_loader


@pytest.fixture
def sample_case():
    loader = get_case_loader()
    return loader.get_case("case_01_blackwood_manor")


# -------------------------------------------------------------
# 1. Specialized Tool Unit Tests
# -------------------------------------------------------------

def test_vision_ocr_tool():
    tool = VisionOCREvidenceTool()
    sample_text = """
    CCTV Feed at 08:15 PM shows Sector 4 gate open.
    Security guard confirmed Officer Vance was present at 08:30 PM in Hall A.
    Uncertain sighting: passenger reported possible shadow at 08:45 PM.
    Noise log: routine coffee delivery recorded at 09:00 PM.
    """
    result = tool.run(sample_text)
    assert "=== OCR & VISION TOOL EXTRACTION REPORT ===" in result
    assert "Confirmed Observations" in result
    assert "Uncertain / Low-Confidence Sightings" in result
    assert "08:15 PM" in result or "08:30 PM" in result


def test_networkx_graph_tool():
    tool = NetworkXDependencyTool()
    sample_facts = """
    1. At 14:00, baggage container 402 arrived at gate B12.
    2. At 14:15, security seal was inspected.
    3. At 14:30, sensor alarm triggered at gate B12.
    """
    result = tool.run(sample_facts)
    assert "=== NETWORKX INCIDENT DEPENDENCY GRAPH ===" in result
    assert "Nodes Analyzed:" in result
    assert "Reconstructed Event Timeline & Dependencies:" in result


def test_z3_solver_tool():
    tool = Z3ConstraintSolverTool()
    timeline = """
    14:00 - Flight boarding commenced.
    14:20 - Unscreened baggage container detected at gate B12.
    14:35 - Pre-departure checklist failed due to unscreened cargo.
    """
    rules = [
        "Rule SEC-01: No aircraft may depart with unscreened baggage in cargo hold.",
        "Rule SEC-02: Flights must be held at gate until manual physical rescreening is certified."
    ]
    result = tool.run(timeline, rules)
    assert "=== Z3 CONSTRAINT SOLVER DECISION REPORT ===" in result
    assert "DEDUCED ACTION:" in result
    assert "BLOCKING CONDITION:" in result
    assert "SUPPORTING OPERATIONAL RULES:" in result


# -------------------------------------------------------------
# 2. Individual Prompt Engineering Evaluators
# -------------------------------------------------------------

def test_player_1_prompt_scoring():
    # Weak prompt
    weak_res = evaluate_player_1_prompt("extract facts", "Some extracted facts from case")
    assert weak_res["prompt_score"] <= 5
    assert weak_res["score"] < 14

    # Strong generalized prompt
    strong_prompt = (
        "Extract the relevant facts from the provided visual and textual evidence. "
        "Identify key people, times, locations, objects, and movements. "
        "Distinguish confirmed facts from uncertain information and filter out noise. "
        "Do not infer causes, identities, or the final action."
    )
    strong_res = evaluate_player_1_prompt(strong_prompt, "Detailed extracted facts across sectors and timestamps.")
    assert strong_res["prompt_score"] == 12
    assert strong_res["agent_score"] == 8
    assert strong_res["score"] == 20


def test_player_2_prompt_scoring():
    # Weak prompt
    weak_res = evaluate_player_2_prompt("make timeline", "8:00 event")
    assert weak_res["prompt_score"] <= 4

    # Strong generalized prompt
    strong_prompt = (
        "Using the extracted evidence, reconstruct the incident. "
        "Organize the events in the correct chronological sequence of what happened first and next. "
        "Connect the relevant people, objects, locations, and events. "
        "Identify the key causal dependencies while keeping uncertain relationships separate. "
        "Maintain objective neutrality and do not state final actions."
    )
    strong_res = evaluate_player_2_prompt(strong_prompt, "Reconstructed sequence of events with causal links.")
    assert strong_res["prompt_score"] == 12
    assert strong_res["agent_score"] == 8
    assert strong_res["score"] == 20


def test_player_3_prompt_scoring():
    # Weak prompt
    weak_res = evaluate_player_3_prompt("who is guilty", '{"culprit": "X"}', was_clean_json=True)
    assert weak_res["prompt_score"] <= 6

    # Strong generalized prompt
    strong_prompt = (
        "You are the Logic Decision Agent. Using the reconstructed incident and operational rules, "
        "determine the valid operational action. Identify the supporting rules, current blocking condition, "
        "and resumption condition. Output strictly valid JSON format with keys: culprit, method, clue."
    )
    strong_res = evaluate_player_3_prompt(strong_prompt, '{"culprit": "A", "method": "B", "clue": "C"}', was_clean_json=True)
    assert strong_res["prompt_score"] == 12
    assert strong_res["agent_score"] == 8
    assert strong_res["score"] == 20


# -------------------------------------------------------------
# 3. Calibrated Normal Distribution Across Prompt Quality Tiers
# -------------------------------------------------------------

def test_calibrated_normal_distribution_tiers(sample_case):
    gt = sample_case.ground_truth.model_dump()

    # Tier 1: Weak prompts (Low score: ~25 - 40)
    p1_tier1 = "get evidence"
    p2_tier1 = "make timeline"
    p3_tier1 = "give answer"
    verdict_tier1 = {
        "culprit": "Charles Blackwood",
        "method": "Arsenic in tea",
        "clue": "Torn letter",
    }
    res_tier1 = evaluate_verdict(
        final_verdict=verdict_tier1,
        ground_truth=gt,
        user_1_prompt=p1_tier1,
        agent_1_output="Basic fact",
        user_2_prompt=p2_tier1,
        agent_2_output="Basic time",
        user_3_prompt=p3_tier1,
        agent_3_output='{"culprit": "Charles Blackwood"}',
        was_clean_json=True,
    )
    assert 15 <= res_tier1["total_score"] <= 40

    # Tier 2: Moderate prompts (Bell Curve Center: ~50 - 70)
    p1_tier2 = "Extract the key people, times, and confirmed observations from the case file."
    p2_tier2 = "Organize what happened first and what happened next in chronological sequence."
    p3_tier2 = "Analyze the timeline against rules to deduce the culprit and method. Output JSON."
    verdict_tier2 = {
        "culprit": gt["culprit"],
        "method": "Poisoning",
        "clue": "Unknown",
    }
    res_tier2 = evaluate_verdict(
        final_verdict=verdict_tier2,
        ground_truth=gt,
        user_1_prompt=p1_tier2,
        agent_1_output="Extracted people: Arthur Bell, Reginald. Times: 8:00 PM, 8:30 PM.",
        user_2_prompt=p2_tier2,
        agent_2_output="8:00 PM tea served. 8:30 PM lights out. 9:15 PM found.",
        user_3_prompt=p3_tier2,
        agent_3_output=f'{{"culprit": "{gt["culprit"]}", "method": "Poisoning", "clue": "Unknown"}}',
        was_clean_json=True,
    )
    assert 50 <= res_tier2["total_score"] <= 75

    # Tier 3: Strong prompts (High score: ~75 - 90)
    p1_tier3 = (
        "Extract relevant facts from visual evidence. Identify key people, times, locations, and movements, "
        "distinguishing confirmed facts from uncertain information. Do not infer causes or actions."
    )
    p2_tier3 = (
        "Reconstruct the incident by organizing events chronologically. Connect relevant people and events, "
        "identifying key dependencies while keeping uncertain relations separate."
    )
    p3_tier3 = (
        "Using the reconstructed incident and rules, determine the culprit and method. "
        "Identify the supporting rules and key clue. Output JSON format."
    )
    verdict_tier3 = {
        "culprit": gt["culprit"],
        "method": gt["weapon_or_method"],
        "clue": "Footprints near door",
    }
    res_tier3 = evaluate_verdict(
        final_verdict=verdict_tier3,
        ground_truth=gt,
        user_1_prompt=p1_tier3,
        agent_1_output="Comprehensive extracted facts across sectors.",
        user_2_prompt=p2_tier3,
        agent_2_output="Detailed chronological sequence with dependencies.",
        user_3_prompt=p3_tier3,
        agent_3_output=f'{{"culprit": "{gt["culprit"]}", "method": "{gt["weapon_or_method"]}", "clue": "Footprints"}}',
        was_clean_json=True,
    )
    assert 75 <= res_tier3["total_score"] <= 90

    # Tier 4: Perfect/Ideal prompts (Top score: ~95 - 100)
    p1_tier4 = (
        "Role: Evidence Extractor. Extract relevant facts from the provided visual and textual evidence. "
        "Identify key people, times, locations, objects, and movements. Distinguish confirmed facts from "
        "uncertain information and ignore irrelevant noise. Do not infer causes, identities, or actions."
    )
    p2_tier4 = (
        "Role: Incident Reconstructor. Reconstruct the incident chronologically. Connect relevant people, "
        "locations, and movements. Identify key causal dependencies while keeping uncertain relationships "
        "strictly separate. Remain objective and do not make final operational decisions."
    )
    p3_tier4 = (
        "Role: Logic Decision Solver. Analyze the reconstructed incident and operational rules to determine "
        "the valid operational action. Identify supporting rules, blocking condition, and resumption condition. "
        "Output strictly valid JSON with keys: culprit, method, clue."
    )
    verdict_tier4 = {
        "culprit": gt["culprit"],
        "method": gt["weapon_or_method"],
        "clue": gt["key_clue"],
    }
    res_tier4 = evaluate_verdict(
        final_verdict=verdict_tier4,
        ground_truth=gt,
        user_1_prompt=p1_tier4,
        agent_1_output="Complete structured extracted facts.",
        user_2_prompt=p2_tier4,
        agent_2_output="Complete chronological graph with causal links.",
        user_3_prompt=p3_tier4,
        agent_3_output='{"culprit": "...", "method": "...", "clue": "..."}',
        was_clean_json=True,
    )
    assert res_tier4["total_score"] >= 95
