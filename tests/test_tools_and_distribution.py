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
    return loader.get_case("case_04_airport_crisis")


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
        "Role: Incident Reconstructor. Reconstruct the incident chronologically into a sequence of what happened first and next. "
        "Connect relevant people, locations, and movements. Identify key causal dependencies while keeping uncertain relationships "
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


def test_airport_crisis_tier5_master_detective_evaluation():
    from backend.app.services.scenario_loader import get_scenario_loader
    from backend.app.graph.evaluator import parse_json_verdict

    loader = get_scenario_loader()
    scenario = loader.get("scenario_01_airport_crisis")
    gt = scenario.ground_truth.model_dump()

    # Tier 5 prompt outputs for Airport Crisis (Flight SW 472)
    p1 = (
        "Role: Forensic Evidence Extractor. "
        "Extract all factual evidence from CCTV, FIDS displays, baggage tags, and reports: "
        "- Entities: passengers (Daniel Kim), officers, and gate personnel "
        "- Times: exact camera and log timestamps "
        "- Locations: Check-in Island A, Gate B07, Apron Bay "
        "- Objects: blue hard-shell suitcase, baggage tag SKW-78921-472. "
        "Distinguish confirmed records from unverified chat observations. "
        "Filter out irrelevant marathon news. Do not decide dispatch actions."
    )
    p2 = (
        "Role: Timeline & Incident Reconstructor. "
        "Reconstruct the Gate B07 security incident into an exact chronological sequence: "
        "- Sequence events by what occurred first, next, and last (08:14 check-in through 09:02 apron loading) "
        "- Trace the unattended blue bag from check-in counter to Gate B07 window seating "
        "- Connect causal links between unattended luggage and pre-departure boarding holds. "
        "Keep uncertain sightings separate. Maintain neutrality without issuing dispatch commands."
    )
    p3 = (
        "Role: Logic Decision Solver. "
        "Evaluate the reconstructed incident timeline against Airport Operational Rules (SEC-101, OPS-204, CLR-305) "
        "to determine the valid operational action: "
        "- Specify the required operational dispatch action (HOLD Flight SW 472 at Gate B07 immediately, suspend boarding, cordon seating, dispatch K9) "
        "- Cite supporting rules (SEC-101, OPS-204) "
        "- State the blocking condition (unattended blue suitcase awaiting K9 sweep) "
        "Output strictly valid JSON with keys: culprit, method, motive, rule_broken, evidence_keys"
    )

    raw_agent3_json = """
    {
      "culprit": "HOLD Flight SW 472 at Gate B07 immediately, suspend boarding, cordon seating, dispatch K9",
      "method": "Rule SEC-101 and Rule OPS-204",
      "motive": "unattended blue suitcase awaiting K9 sweep",
      "rule_broken": "SEC-101, OPS-204",
      "evidence_keys": [
        "08:46 passenger report of unattended blue suitcase at Gate B07",
        "08:47:10 CCTV CAM 12 unidentified hooded individual fleeing Gate B07",
        "08:49:00 Security Incident Log #SEC-0849 established",
        "Bag tag #SKW-78921-472 check-in logistics discrepancy"
      ]
    }
    """
    parsed_verdict, was_clean = parse_json_verdict(raw_agent3_json)

    res = evaluate_verdict(
        final_verdict=parsed_verdict,
        ground_truth=gt,
        user_1_prompt=p1,
        agent_1_output="Verified factual observations extracted.",
        user_2_prompt=p2,
        agent_2_output="Chronological timeline with causal links.",
        user_3_prompt=p3,
        agent_3_output=raw_agent3_json,
        was_clean_json=was_clean,
    )

    # Must achieve Master Detective score (>= 90 pts)
    assert res["total_score"] >= 95
    assert res["grade"] == "Master Detective (S)"

    # Culprit / operational action must be fully credited (15/15)
    assert res["breakdown"]["culprit"]["status"] == "correct"
    assert res["breakdown"]["culprit"]["points"] == 15

    # Method / rules must be fully credited (15/15)
    assert res["breakdown"]["method"]["status"] == "correct"
    assert res["breakdown"]["method"]["points"] == 15

    # Clue extracted from evidence_keys must be correctly recognized (10/10)
    assert res["breakdown"]["clue"]["status"] == "correct"
    assert res["breakdown"]["clue"]["points"] == 10


def test_airport_crisis_all_five_tiers_distribution():
    """Verify that Tiers 1 through 5 produce monotonic scores strictly within their designated grade brackets."""
    from backend.app.services.scenario_loader import get_scenario_loader
    from backend.app.graph.nodes import node_extractor, node_reconstructor, node_solver
    from backend.app.graph.evaluator import parse_json_verdict, evaluate_verdict
    from backend.app.core.llm import MockOfflineChatModel

    loader = get_scenario_loader()
    scenario = loader.get("scenario_01_airport_crisis")
    gt = scenario.ground_truth.model_dump()
    mock_llm = MockOfflineChatModel()

    tiers_data = {
        "Tier 1": {
            "p1": "look at the airport evidence and tell me what happened with flight 472.",
            "p2": "make a timeline of the airport events.",
            "p3": "who is guilty at gate B07? tell me what to do.",
            "min_score": 0,
            "max_score": 39,
            "expected_grade": "Unsolved (F)",
        },
        "Tier 2": {
            "p1": "Examine the airport evidence. Extract the people, gates, and luggage from the CCTV files.",
            "p2": "Organize the Gate B07 events in chronological sequence of what happened first and next.",
            "p3": "Analyze the situation at Gate B07 to determine the security action. Output in JSON format.",
            "min_score": 40,
            "max_score": 59,
            "expected_grade": "Apprentice (C)",
        },
        "Tier 3": {
            "p1": "You are the evidence extractor. Extract the facts regarding Flight SW 472: identify people, locations, objects, and baggage. Record what occurred at Counter A04 and Gate B07.",
            "p2": "You are the incident reconstructor. Organize all extracted airport events in chronological order: trace Daniel Kim and the blue bag from check-in to Gate B07.",
            "p3": "You are the decision agent. Analyze the Gate B07 timeline against airport operational protocols. Determine the security hold action for Flight SW 472. Output JSON format with keys: culprit, method, clue.",
            "min_score": 60,
            "max_score": 74,
            "expected_grade": "Investigator (B)",
        },
        "Tier 4": {
            "p1": "Role: Evidence Extractor. Extract verified facts from CCTV and incident logs: identify passengers, gate locations, and baggage. Distinguish confirmed facts from unverified passenger observations.",
            "p2": "Role: Incident Reconstructor. Synthesize facts into a chronological sequence from 08:14 to 09:02. Connect causal links between the unattended bag and boarding status.",
            "p3": "Role: Logic Decision Solver. Evaluate the timeline against Airport Operational Rules (SEC-101, OPS-204) to determine the operational dispatch action. Output strictly valid JSON format with keys: culprit, method, clue.",
            "min_score": 75,
            "max_score": 89,
            "expected_grade": "Senior Sleuth (A)",
        },
        "Tier 5": {
            "p1": (
                "Role: Forensic Evidence Extractor. "
                "Extract all factual evidence from CCTV, FIDS displays, baggage tags, and reports: "
                "- Entities: passengers (Daniel Kim), officers, and gate personnel "
                "- Times: exact camera and log timestamps "
                "- Locations: Check-in Island A, Gate B07, Apron Bay "
                "- Objects: blue hard-shell suitcase, baggage tag SKW-78921-472. "
                "Distinguish confirmed records from unverified chat observations. "
                "Filter out irrelevant marathon news. Do not decide dispatch actions."
            ),
            "p2": (
                "Role: Timeline & Incident Reconstructor. "
                "Reconstruct the Gate B07 security incident into an exact chronological sequence: "
                "- Sequence events by what occurred first, next, and last (08:14 check-in through 09:02 apron loading) "
                "- Trace the unattended blue bag from check-in counter to Gate B07 window seating "
                "- Connect causal links between unattended luggage and pre-departure boarding holds. "
                "Keep uncertain sightings separate. Maintain neutrality without issuing dispatch commands."
            ),
            "p3": (
                "Role: Logic Decision Solver. "
                "Evaluate the reconstructed incident timeline against Airport Operational Rules (SEC-101, OPS-204, CLR-305) "
                "to determine the valid operational action: "
                "- Specify the required operational dispatch action (HOLD Flight SW 472 at Gate B07 immediately, suspend boarding, cordon seating, dispatch K9) "
                "- Cite supporting rules (SEC-101, OPS-204) "
                "- State the blocking condition (unattended blue suitcase awaiting K9 sweep) "
                "Output strictly valid JSON with keys: culprit, method, motive, rule_broken, evidence_keys"
            ),
            "min_score": 90,
            "max_score": 100,
            "expected_grade": "Master Detective (S)",
        },
    }

    scores = []
    for tier_name, data in tiers_data.items():
        state = {
            "scenario": scenario,
            "p1_prompt": data["p1"],
            "p2_prompt": data["p2"],
            "p3_prompt": data["p3"],
            "leak_keywords": scenario.spoiler_keywords,
        }
        res1 = node_extractor(state, llm=mock_llm)
        state.update(res1)
        res2 = node_reconstructor(state, llm=mock_llm)
        state.update(res2)
        res3 = node_solver(state, llm=mock_llm)
        state.update(res3)

        parsed_verdict, was_clean = parse_json_verdict(state["agent_3_output"])
        res = evaluate_verdict(
            final_verdict=parsed_verdict,
            ground_truth=gt,
            leak_detected=False,
            was_clean_json=was_clean,
            user_1_prompt=data["p1"],
            agent_1_output=state["agent_1_output"],
            user_2_prompt=data["p2"],
            agent_2_output=state["agent_2_output"],
            user_3_prompt=data["p3"],
            agent_3_output=state["agent_3_output"],
        )

        total = res["total_score"]
        scores.append(total)
        assert data["min_score"] <= total <= data["max_score"], (
            f"{tier_name} score {total} out of expected range [{data['min_score']}, {data['max_score']}]"
        )
        assert res["grade"] == data["expected_grade"], (
            f"{tier_name} grade {res['grade']} does not match expected {data['expected_grade']}"
        )

    # Monotonic progression across tiers
    for i in range(len(scores) - 1):
        assert scores[i] < scores[i + 1], f"Scores should strictly increase across tiers: {scores}"


def test_image_scenarios_structural_parity():
    """Verify that both image-based stories have 10 evidence items, operational rules, and ground truth."""
    from backend.app.services.scenario_loader import get_scenario_loader

    loader = get_scenario_loader()
    image_scenario_ids = [
        "scenario_01_airport_crisis",
        "scenario_05_museum_heist",
    ]

    for s_id in image_scenario_ids:
        scenario = loader.get(s_id)
        assert scenario is not None, f"Scenario {s_id} not found"
        assert scenario.type == "image", f"[{s_id}] Expected type 'image', got '{scenario.type}'"
        assert len(scenario.evidence_items) == 10, f"[{s_id}] Expected 10 evidence items, got {len(scenario.evidence_items)}"
        assert len(scenario.operational_rules) == 3, f"[{s_id}] Expected 3 operational rules, got {len(scenario.operational_rules)}"
        assert scenario.ground_truth is not None, f"[{s_id}] Ground truth must not be None"


def test_museum_heist_tier5_master_detective_evaluation():
    from backend.app.services.scenario_loader import get_scenario_loader
    from backend.app.graph.evaluator import parse_json_verdict, evaluate_verdict

    loader = get_scenario_loader()
    scenario = loader.get("scenario_05_museum_heist")
    assert scenario is not None
    gt = scenario.ground_truth.model_dump()

    p1 = (
        "Role: Forensic Evidence Extractor. "
        "Extract all factual evidence from CCTV, SCADA telemetry, blueprints, and logs: "
        "- Entities: Dr. Julian Vance, Chief Marcus Thorne, Officer Carter "
        "- Times: exact SCADA and camera timestamps "
        "- Locations: Gallery 4, Stairwell C1, Locker 14 "
        "- Objects: framed Madonna RM-1887-04, canvas tube, Cloakroom token C-408, card CONSV-408. "
        "Distinguish confirmed facts from unverified rumors. "
        "Filter out dropped champagne crate noise. Do not accuse anyone."
    )
    p2 = (
        "Role: Timeline & Incident Reconstructor. "
        "Reconstruct the museum heist into a strict chronological sequence: "
        "- Sequence events by what occurred first, next, and last (21:15 gala entry through 23:48 locker search) "
        "- Trace suspect movements and connect causal dependencies linking the 23:40:42 Breaker B-04 blackout to the canvas forgery swap and Locker 14 drop. "
        "Keep uncertain sightings separate. Maintain neutrality without naming a culprit."
    )
    p3 = (
        "Role: Logic Decision Solver. "
        "Analyze the reconstructed timeline against Museum Art Crime Rules (Rule SEC-401, Rule ART-302, Rule CLR-505) "
        "to determine the final resolution: "
        "- Deduce the true conspirators (Dr. Julian Vance and Marcus Thorne) "
        "- Explain the Breaker B-04 90-second blackout canvas forgery swap method "
        "- Identify decisive evidence_keys (Conservation RFID card CONSV-408 and token C-408 in Locker 14, Thorne sub-station sabotage alibi contradiction, acrylic spectrometry). "
        "Output strictly valid JSON with keys: culprit, method, motive, rule_broken, evidence_keys"
    )

    raw_agent3_json = """
    {
      "culprit": "Dr. Julian Vance (Head of Conservation) and Chief Marcus Thorne (Security Accomplice)",
      "method": "Breaker B-04 intentional blackout exploiting 90-second auxiliary power failover to swap original canvas with synthetic acrylic forgery and drop tube at Locker 14 under Rule SEC-401 and Rule ART-302",
      "rule_broken": "Rule SEC-401, Rule ART-302, and Rule CLR-505",
      "clue": "Locker 14 search yielded Conservation RFID keycard CONSV-408 and Private Vault cloakroom token C-408 matching Julian Vance, disproving Thorne's sub-station sabotage alibi and proving canvas swap forgery RM-1887-04",
      "motive": "Replace authentic Renaissance masterpiece with synthetic acrylic forgery for illicit high-value private sale",
      "evidence_keys": [
        "Recovered Conservation staff access card #408 (CONSV-408) and Gala Cloakroom token No. C-408 from Locker 14",
        "Lab spectrometry confirming wall painting RM-1887-04 is a 2023 synthetic acrylic forgery with zinc white",
        "SCADA telemetry and Evidence #04 memo confirming Breaker B-04 trip 90-second blackout loop",
        "Thorne sub-station sabotage alibi disproven by insider timing and Locker 14 drop"
      ]
    }
    """
    parsed_verdict, was_clean = parse_json_verdict(raw_agent3_json)

    res = evaluate_verdict(
        final_verdict=parsed_verdict,
        ground_truth=gt,
        user_1_prompt=p1,
        agent_1_output="Verified factual observations extracted.",
        user_2_prompt=p2,
        agent_2_output="Chronological timeline with causal links.",
        user_3_prompt=p3,
        agent_3_output=raw_agent3_json,
        was_clean_json=was_clean,
    )

    assert res["total_score"] >= 95
    assert res["grade"] == "Master Detective (S)"
    assert res["breakdown"]["culprit"]["status"] == "correct"
    assert res["breakdown"]["culprit"]["points"] == 15
    assert res["breakdown"]["method"]["status"] == "correct"
    assert res["breakdown"]["method"]["points"] == 15
    assert res["breakdown"]["clue"]["status"] == "correct"
    assert res["breakdown"]["clue"]["points"] == 10


def test_museum_heist_all_five_tiers_distribution():
    """Verify that Tiers 1 through 5 for Riverton Museum Heist produce monotonic scores strictly within their designated grade brackets."""
    from backend.app.services.scenario_loader import get_scenario_loader
    from backend.app.graph.nodes import node_extractor, node_reconstructor, node_solver
    from backend.app.graph.evaluator import parse_json_verdict, evaluate_verdict
    from backend.app.core.llm import MockOfflineChatModel

    loader = get_scenario_loader()
    scenario = loader.get("scenario_05_museum_heist")
    assert scenario is not None
    gt = scenario.ground_truth.model_dump()
    mock_llm = MockOfflineChatModel()

    tiers_data = {
        "Tier 1": {
            "p1": "look at the museum evidence and tell me what happened to the painting.",
            "p2": "make a timeline of the museum events.",
            "p3": "who stole the painting? tell me what to do.",
            "min_score": 0,
            "max_score": 39,
            "expected_grade": "Unsolved (F)",
        },
        "Tier 2": {
            "p1": "Examine the museum evidence. Extract the people, galleries, and art items from the CCTV files.",
            "p2": "Organize the Gallery 4 events in chronological sequence of what happened first and next.",
            "p3": "Analyze the situation in Gallery 4 to determine the culprit and action taken. Output in JSON format.",
            "min_score": 40,
            "max_score": 59,
            "expected_grade": "Apprentice (C)",
        },
        "Tier 3": {
            "p1": "You are the evidence extractor. Extract the facts regarding Riverton Museum: identify people, locations, objects, and timestamps. Record what occurred in Gallery 4 and the basement passage.",
            "p2": "You are the incident reconstructor. Organize all extracted museum events in chronological order: trace Dr. Vance, Chief Thorne, and the canvas tube from Gallery 4 to the basement corridor.",
            "p3": "You are the decision agent. Analyze the museum timeline against art crime protocols. Determine the culprit and method for the painting theft. Output JSON format with keys: culprit, method, clue.",
            "min_score": 60,
            "max_score": 74,
            "expected_grade": "Investigator (B)",
        },
        "Tier 4": {
            "p1": "Role: Evidence Extractor. Extract verified facts from CCTV and SCADA logs: identify museum staff, gallery locations, and telemetry. Distinguish confirmed facts from unverified catering noise.",
            "p2": "Role: Incident Reconstructor. Synthesize facts into a chronological sequence from 21:15 to 23:55. Connect causal links between the breaker trip and the canvas tube transit.",
            "p3": "Role: Logic Decision Solver. Evaluate the timeline against Museum Protocols (Rule SEC-401, Rule ART-302) to determine the culprit and method. Output strictly valid JSON format with keys: culprit, method, clue.",
            "min_score": 75,
            "max_score": 89,
            "expected_grade": "Senior Sleuth (A)",
        },
        "Tier 5": {
            "p1": (
                "Role: Forensic Evidence Extractor. "
                "Extract all factual evidence from CCTV, SCADA telemetry, blueprints, and logs: "
                "- Entities: Dr. Julian Vance, Chief Marcus Thorne, Officer Carter "
                "- Times: exact SCADA and camera timestamps "
                "- Locations: Gallery 4, Stairwell C1, Locker 14 "
                "- Objects: framed Madonna RM-1887-04, canvas tube, Cloakroom token C-408, card CONSV-408. "
                "Distinguish confirmed facts from unverified rumors. "
                "Filter out dropped champagne crate noise. Do not accuse anyone."
            ),
            "p2": (
                "Role: Timeline & Incident Reconstructor. "
                "Reconstruct the museum heist into a strict chronological sequence: "
                "- Sequence events by what occurred first, next, and last (21:15 gala entry through 23:48 locker search) "
                "- Trace suspect movements and connect causal dependencies linking the 23:40:42 Breaker B-04 blackout to the canvas forgery swap and Locker 14 drop. "
                "Keep uncertain sightings separate. Maintain neutrality without naming a culprit."
            ),
            "p3": (
                "Role: Logic Decision Solver. "
                "Analyze the reconstructed timeline against Museum Art Crime Rules (Rule SEC-401, Rule ART-302, Rule CLR-505) "
                "to determine the final resolution: "
                "- Deduce the true conspirators (Dr. Julian Vance and Marcus Thorne) "
                "- Explain the Breaker B-04 90-second blackout canvas forgery swap method "
                "- Identify decisive evidence_keys (Conservation RFID card CONSV-408 and token C-408 in Locker 14, Thorne sub-station sabotage alibi contradiction, acrylic spectrometry). "
                "Output strictly valid JSON with keys: culprit, method, motive, rule_broken, evidence_keys"
            ),
            "min_score": 90,
            "max_score": 100,
            "expected_grade": "Master Detective (S)",
        },
    }

    scores = []
    for tier_name, data in tiers_data.items():
        state = {
            "scenario": scenario,
            "p1_prompt": data["p1"],
            "p2_prompt": data["p2"],
            "p3_prompt": data["p3"],
            "leak_keywords": scenario.spoiler_keywords,
        }
        res1 = node_extractor(state, llm=mock_llm)
        state.update(res1)
        res2 = node_reconstructor(state, llm=mock_llm)
        state.update(res2)
        res3 = node_solver(state, llm=mock_llm)
        state.update(res3)

        parsed_verdict, was_clean = parse_json_verdict(state["agent_3_output"])
        res = evaluate_verdict(
            final_verdict=parsed_verdict,
            ground_truth=gt,
            leak_detected=False,
            was_clean_json=was_clean,
            user_1_prompt=data["p1"],
            agent_1_output=state["agent_1_output"],
            user_2_prompt=data["p2"],
            agent_2_output=state["agent_2_output"],
            user_3_prompt=data["p3"],
            agent_3_output=state["agent_3_output"],
        )

        total = res["total_score"]
        scores.append(total)
        assert data["min_score"] <= total <= data["max_score"], (
            f"{tier_name} score {total} out of expected range [{data['min_score']}, {data['max_score']}]"
        )
        assert res["grade"] == data["expected_grade"], (
            f"{tier_name} grade {res['grade']} does not match expected {data['expected_grade']}"
        )

    # Monotonic progression across tiers
    for i in range(len(scores) - 1):
        assert scores[i] < scores[i + 1], f"Scores should strictly increase across tiers: {scores}"




