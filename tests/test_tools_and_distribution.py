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


def test_mafia_scenarios_all_five_tiers_distribution():
    """Verify that text-based murder mystery scenarios (Blackwood, Neon Nexus, Velvet Vault) strictly follow the 5-tier score brackets."""
    from backend.app.services.scenario_loader import get_scenario_loader
    from backend.app.graph.nodes import node_extractor, node_reconstructor, node_solver
    from backend.app.graph.evaluator import parse_json_verdict, evaluate_verdict
    from backend.app.core.llm import MockOfflineChatModel

    loader = get_scenario_loader()
    mock_llm = MockOfflineChatModel()

    scenarios = [
        "scenario_02_blackwood_manor",
        "scenario_03_neon_nexus",
        "scenario_04_velvet_vault",
    ]

    for s_id in scenarios:
        scenario = loader.get(s_id)
        gt = scenario.ground_truth.model_dump()

        # Build scenario-specific tier definitions
        if s_id == "scenario_02_blackwood_manor":
            p1_t2 = "Examine the evidence file. Extract the people, rooms, and tea items from the records."
            p2_t2 = "Organize the manor events in chronological sequence of what happened first and next."
            p3_t2 = "Analyze the situation at the manor to determine the culprit and action taken. Output in JSON format."

            p1_t3 = "You are the evidence extractor. Extract the facts regarding Blackwood Manor: identify people, times, locations, and tea items. Record what occurred in the drawing room and study."
            p2_t3 = "You are the incident reconstructor. Organize all extracted manor events in chronological order: trace Dr. Bell and the tea tray from the drawing room to the study."
            p3_t3 = "You are the decision agent. Analyze the manor timeline against forensic protocols. Determine the culprit and method for Lord Reginald's death. Output JSON format with keys: culprit, method, clue."

            p1_t4 = "Role: Evidence Extractor. Extract verified facts from the manor dossier: identify people, room locations, and tea items. Distinguish confirmed facts from unverified staff rumors."
            p2_t4 = "Role: Incident Reconstructor. Synthesize facts into a chronological sequence from 8:00 to 9:15 PM. Connect causal links between the unattended tea tray and poisoning."
            p3_t4 = "Role: Logic Decision Solver. Evaluate the timeline against Forensic Trace Standard §102 and Timeline Discrepancy Principle to determine the culprit and method. Output strictly valid JSON format with keys: culprit, method, clue."

            p1_t5 = (
                "Role: Forensic Evidence Extractor. Extract all verified facts from the dossier and evidence feeds: "
                "identify people (Dr. Bell, Higgins, Charles, Beatrice), timestamps (8:00 to 9:15 PM), "
                "locations (study, cellar, drawing room, greenhouse), and objects (Earl Grey tea, Demerara sugar, silver sugar tongs, muddy boots). "
                "Distinguish confirmed facts from uncertain observations. Ignore kitchen fire chatter. Do not accuse anyone."
            )
            p2_t5 = (
                "Role: Timeline & Incident Reconstructor. Using the extracted facts, reconstruct the incident into a strict chronological sequence: "
                "order events by what happened first, next, and last with exact timestamps from 8:00 PM tea preparation to 9:15 PM discovery. "
                "Trace suspect movements and connect causal dependencies showing how the unattended tea tray allowed poison delivery. "
                "Keep uncertain sightings separate. Maintain neutrality without naming a culprit."
            )
            p3_t5 = (
                "Role: Logic Decision Solver. Analyze the reconstructed timeline alongside operational rules (Forensic Trace Standard §102, Timeline Discrepancy Principle) "
                "to determine the final resolution: deduce the true culprit, explain the potassium cyanide sugar tongs method, "
                "and identify decisive physical evidence_keys (red peat mud boots greenhouse alibi contradiction and sugar tongs residue). "
                "Output strictly valid JSON with keys: culprit, method, motive, rule_broken, evidence_keys"
            )
        elif s_id == "scenario_03_neon_nexus":
            p1_t2 = "Examine the cleanroom evidence. Extract the engineers, server rooms, and medical devices."
            p2_t2 = "Organize the cleanroom events in chronological sequence of what happened first and next."
            p3_t2 = "Analyze the situation in the cleanroom to determine the culprit and action taken. Output in JSON format."

            p1_t3 = "You are the evidence extractor. Extract the facts regarding SynthAI cleanroom: identify people, times, locations, and medical devices. Record what occurred in Cleanroom 03 and server pods."
            p2_t3 = "You are the incident reconstructor. Organize all extracted cleanroom events in chronological order: trace Marcus Vance and the insulin pump from the cleanroom to the lounge."
            p3_t3 = "You are the decision agent. Analyze the cleanroom timeline against cyber-physical protocols. Determine the culprit and method for Dr. Rostova's death. Output JSON format with keys: culprit, method, clue."

            p1_t4 = "Role: Evidence Extractor. Extract verified facts from cleanroom logs and device telemetry: identify engineers, server rooms, and medical devices. Distinguish confirmed facts from unverified statements."
            p2_t4 = "Role: Incident Reconstructor. Synthesize facts into a chronological sequence from 22:00 to 23:45. Connect causal links between the wireless transmission and pump bolus."
            p3_t4 = "Role: Logic Decision Solver. Evaluate the timeline against Cyber-Physical Forensics Standard §404 and Alibi Integrity Rule to determine the culprit and method. Output strictly valid JSON format with keys: culprit, method, clue."

            p1_t5 = (
                "Role: Forensic Evidence Extractor. Extract all verified facts from the dossier and evidence feeds: "
                "identify people (Marcus Vance, Dr. Elena Rostova, Chloe Lin), timestamps (22:00 to 23:45), "
                "locations (Class-10 cleanroom, cubicles, lounge), and objects (Omnipod insulin pump, BLE sniffer, Pi Zero dongle, USB power bank). "
                "Distinguish confirmed logs from unverified statements. Ignore cooling manifold noise. Do not accuse anyone."
            )
            p2_t5 = (
                "Role: Timeline & Incident Reconstructor. Using the extracted facts, reconstruct the incident into a strict chronological sequence: "
                "order events by what happened first, next, and last with exact timestamps from 22:15 entry to 23:45 discovery. "
                "Trace suspect movements and connect causal dependencies linking the 22:42:14 BLE transmission to the fatal insulin bolus. "
                "Keep unverified alibis separate. Maintain neutrality without naming a culprit."
            )
            p3_t5 = (
                "Role: Logic Decision Solver. Analyze the reconstructed timeline alongside operational rules (Cyber-Physical Forensics Standard §404, Alibi Integrity Rule) "
                "to determine the final resolution: deduce the true culprit, explain the remote BLE insulin override method, "
                "and identify decisive evidence_keys (concealed Pi Zero MAC D4:8A:3F:11:C9:82 in drawer and automated cron commit alibi contradiction). "
                "Output strictly valid JSON with keys: culprit, method, motive, rule_broken, evidence_keys"
            )
        else:  # scenario_04_velvet_vault
            p1_t2 = "Examine the gallery evidence. Extract the guests, display vitrines, and art pieces."
            p2_t2 = "Organize the gallery events in chronological sequence of what happened first and next."
            p3_t2 = "Analyze the situation at the gallery to determine the culprit and action taken. Output in JSON format."

            p1_t3 = "You are the evidence extractor. Extract the facts regarding Vernissage Gallery: identify people, times, locations, and vitrines. Record what occurred in the private vault and Grand Rotunda."
            p2_t3 = "You are the incident reconstructor. Organize all extracted gallery events in chronological order: trace Julian Thorne and the display vitrine from the rotunda to the vault."
            p3_t3 = "You are the decision agent. Analyze the gallery timeline against forensic art crime protocols. Determine the culprit and method for Delacroix's death. Output JSON format with keys: culprit, method, clue."

            p1_t4 = "Role: Evidence Extractor. Extract verified facts from gallery dossiers and toxicology reports: identify guests, vault locations, and vitrines. Distinguish confirmed facts from unverified observations."
            p2_t4 = "Role: Incident Reconstructor. Synthesize facts into a chronological sequence from 20:30 to 22:45. Connect causal links between the coated vitrine latch and Delacroix poisoning."
            p3_t4 = "Role: Logic Decision Solver. Evaluate the timeline against Biological Trace Principle §201 and Property Recovery Presumption to determine the culprit and method. Output strictly valid JSON format with keys: culprit, method, clue."

            p1_t5 = (
                "Role: Forensic Evidence Extractor. Extract all verified facts from the dossier and evidence feeds: "
                "identify people (Julian Thorne, Henri Delacroix, Cecile Moreau, Monique De Valois), timestamps (20:30 to 22:45), "
                "locations (Grand Rotunda, private vault, restroom, terrace), and objects (vitrine latch, nitrile gloves, Caesarean Emerald, lavender talc). "
                "Distinguish confirmed facts from uncertain rumors. Ignore broken champagne glass noise. Do not accuse anyone."
            )
            p2_t5 = (
                "Role: Timeline & Incident Reconstructor. Using the extracted facts, reconstruct the incident into a strict chronological sequence: "
                "order events by what happened first, next, and last with exact timestamps from 20:30 preview to 21:40 collapse. "
                "Trace suspect movements and connect causal dependencies showing how the coated vitrine latch caused Delacroix transdermal poisoning. "
                "Keep unverified sightings separate. Maintain neutrality without naming a culprit."
            )
            p3_t5 = (
                "Role: Logic Decision Solver. Analyze the reconstructed timeline alongside operational rules (Biological Trace Principle §201, Property Recovery Presumption) "
                "to determine the final resolution: deduce the true culprit, explain the tetrodotoxin coated vitrine latch method, "
                "and identify decisive evidence_keys (discarded nitrile gloves with Julian Thorne DNA and stolen Caesarean Emerald in briefcase). "
                "Output strictly valid JSON with keys: culprit, method, motive, rule_broken, evidence_keys"
            )

        tiers_data = {
            "Tier 1": {
                "p1": "get evidence from the file and tell me what happened.",
                "p2": "make a timeline of the events.",
                "p3": "who is guilty? give me the answer.",
                "min_score": 0,
                "max_score": 39,
                "expected_grade": "Unsolved (F)",
            },
            "Tier 2": {
                "p1": p1_t2,
                "p2": p2_t2,
                "p3": p3_t2,
                "min_score": 40,
                "max_score": 59,
                "expected_grade": "Apprentice (C)",
            },
            "Tier 3": {
                "p1": p1_t3,
                "p2": p2_t3,
                "p3": p3_t3,
                "min_score": 60,
                "max_score": 74,
                "expected_grade": "Investigator (B)",
            },
            "Tier 4": {
                "p1": p1_t4,
                "p2": p2_t4,
                "p3": p3_t4,
                "min_score": 75,
                "max_score": 89,
                "expected_grade": "Senior Sleuth (A)",
            },
            "Tier 5": {
                "p1": p1_t5,
                "p2": p2_t5,
                "p3": p3_t5,
                "min_score": 90,
                "max_score": 100,
                "expected_grade": "Master Detective (S)",
            },
        }

        scenario_scores = []
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
            scenario_scores.append(total)
            assert data["min_score"] <= total <= data["max_score"], (
                f"[{s_id}] {tier_name} score {total} out of expected range [{data['min_score']}, {data['max_score']}]"
            )
            assert res["grade"] == data["expected_grade"], (
                f"[{s_id}] {tier_name} grade {res['grade']} does not match expected {data['expected_grade']}"
            )

        # Monotonic progression across tiers
        for i in range(len(scenario_scores) - 1):
            assert scenario_scores[i] < scenario_scores[i + 1], (
                f"[{s_id}] Scores should strictly increase across tiers: {scenario_scores}"
            )


def test_text_scenarios_structural_parity():
    """Verify that all three text-based stories have equal difficulty (Hard), 4 suspects, 3 evidence documents, and 3 decoys."""
    from backend.app.services.scenario_loader import get_scenario_loader

    loader = get_scenario_loader()
    text_scenario_ids = [
        "scenario_02_blackwood_manor",
        "scenario_03_neon_nexus",
        "scenario_04_velvet_vault",
    ]

    for s_id in text_scenario_ids:
        scenario = loader.get(s_id)
        assert scenario is not None, f"Scenario {s_id} not found"

        # Equal difficulty
        assert scenario.difficulty == "Hard", f"[{s_id}] Expected difficulty 'Hard', got '{scenario.difficulty}'"

        # 4 suspects
        suspects = scenario.ground_truth.suspects_or_entities
        assert len(suspects) == 4, f"[{s_id}] Expected 4 suspects, got {len(suspects)}: {suspects}"

        # 3 evidence documents
        evidence_items = scenario.evidence_items
        assert len(evidence_items) == 3, f"[{s_id}] Expected 3 evidence items, got {len(evidence_items)}"

        # 3 decoy items
        decoys = scenario.decoy_items
        assert len(decoys) == 3, f"[{s_id}] Expected 3 decoy items, got {len(decoys)}: {decoys}"

        # 2 operational rules
        rules = scenario.operational_rules
        assert len(rules) == 2, f"[{s_id}] Expected 2 operational rules, got {len(rules)}: {rules}"



