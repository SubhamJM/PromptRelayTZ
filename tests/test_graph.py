import json
import pytest
from langchain_core.language_models.fake_chat_models import FakeListChatModel

from backend.app.graph.evaluator import evaluate_verdict, parse_json_verdict
from backend.app.graph.nodes import (
    agent_1_extractor,
    agent_2_reconstructor,
    agent_3_detective,
    agent_evaluator,
)
from backend.app.graph.state import GameState
from backend.app.graph.workflow import create_relay_graph
from backend.app.services.case_loader import get_case_loader


@pytest.fixture
def sample_case():
    loader = get_case_loader()
    return loader.get_case("case_05_museum_heist")


# -------------------------------------------------------------
# 1. JSON Parser Tests
# -------------------------------------------------------------

def test_parse_json_verdict_clean():
    raw = '{"culprit": "Dr. Julian Vance", "method": "Breaker blackout", "clue": "Locker 14"}'
    parsed, was_clean = parse_json_verdict(raw)
    assert was_clean is True
    assert parsed["culprit"] == "Dr. Julian Vance"
    assert parsed["method"] == "Breaker blackout"
    assert parsed["clue"] == "Locker 14"


def test_parse_json_verdict_markdown_fenced():
    raw = '```json\n{"culprit": "Dr. Julian Vance", "method": "Breaker blackout", "clue": "Locker 14"}\n```'
    parsed, was_clean = parse_json_verdict(raw)
    assert was_clean is True
    assert parsed["culprit"] == "Dr. Julian Vance"


def test_parse_json_verdict_conversational_wrapper():
    raw = 'Based on the timeline, here is my verdict:\n{"culprit": "Dr. Julian Vance", "method": "Breaker blackout", "clue": "Locker 14"}\nLet me know if you need more details.'
    parsed, was_clean = parse_json_verdict(raw)
    assert was_clean is False  # Had outside conversational text
    assert parsed["culprit"] == "Dr. Julian Vance"
    assert parsed["method"] == "Breaker blackout"


def test_parse_json_verdict_broken():
    raw = "The killer is definitely Charles because he had the motive!"
    parsed, was_clean = parse_json_verdict(raw)
    assert was_clean is False
    assert parsed["culprit"] == ""


def test_parse_json_verdict_fenced_with_unescaped_newline():
    raw = """Agent 3 Final Verdict:

```json
{
  "culprit": "Tariq Malik (Senior Ramp Baggage Supervisor, Badge #RAMP-882)",
  "method": "Unauthorized duplication of automated baggage tag to create a diversion, deploying a pre-weighted ballast decoy bag at Gate B07, and intercepting authentic high-value cargo at Apron Bay 3",
  "motive": "Theft and illegal diversion of Customs Consignment #DIA-904 ($3.5M in uncut diamonds)",
  "rule_broken": "SEC-101, BAGG-204, OPS-204",
  "evidence_keys": [
    "08:16:05 - Fraudulent duplicate tag #\nSKW-78921-472 generated using override REPRINT-MGR-02 under Badge #RAMP-882",
    "08:47:45 - Keycard swipe by Badge #RAMP-882 at door B-Staff-03 following decoy drop",
    "08:49:00 - Weight discrepancy of 6.3 kg (18.4 kg check-in vs. 12.1 kg decoy bag containing sand/gravel)",
    "09:02:55 - CAM 21 video capture of Malik stashing real diamond consignment in Maintenance Cart #MC-08",
    "Handwritten drop memo recovered at Gate B07 matching Tariq Malik's official signature referencing Cart 08"
  ]
}
```
"""
    parsed, was_clean = parse_json_verdict(raw)
    assert "Tariq Malik" in parsed["culprit"]
    assert "Unauthorized duplication" in parsed["method"]
    assert "SEC-101" in parsed["rule_broken"]
    assert len(parsed["evidence_keys"]) == 5


# -------------------------------------------------------------
# 2. Analytical Evaluator Tests
# -------------------------------------------------------------

def test_evaluator_perfect_score(sample_case):
    verdict = {
        "culprit": "Dr. Julian Vance",
        "method": "Breaker B-04 intentional blackout exploiting 90-second auxiliary power failover to swap original canvas with synthetic acrylic forgery and drop tube at Locker 14 under Rule SEC-401 and Rule ART-302",
        "clue": "Conservation staff access card CONSV-408 and Private Vault cloakroom token C-408 recovered from Locker 14, matching Dr. Julian Vance (Badge CONSV-04 / Conservation), Thorne's sub-station sabotage alibi contradiction, and modern acrylic forgery RM-1887-04",
    }
    result = evaluate_verdict(
        final_verdict=verdict,
        ground_truth=sample_case.ground_truth.model_dump(),
        leak_detected=False,
        was_clean_json=True,
    )
    assert result["total_score"] == 100
    assert result["grade"] == "Master Detective (S)"
    assert result["breakdown"]["culprit"]["points"] == 40
    assert result["breakdown"]["method"]["points"] == 25
    assert result["breakdown"]["clue"]["points"] == 20
    assert result["breakdown"]["format"]["points"] == 15
    assert result["breakdown"]["guardrail_status"]["enforced"] is True


def test_evaluator_wrong_culprit(sample_case):
    verdict = {
        "culprit": "Officer J. Carter",
        "method": "Unlocked gate",
        "clue": "Dropped keys",
    }
    result = evaluate_verdict(
        final_verdict=verdict,
        ground_truth=sample_case.ground_truth.model_dump(),
        leak_detected=False,
        was_clean_json=True,
    )
    assert result["breakdown"]["culprit"]["points"] == 0
    assert result["breakdown"]["culprit"]["status"] == "incorrect"
    assert result["total_score"] < 60


def test_evaluator_pure_merit_score(sample_case):
    verdict = {
        "culprit": "Dr. Julian Vance",
        "method": "Breaker B-04 intentional blackout to swap canvas with synthetic acrylic forgery and drop tube at Locker 14 under Rule SEC-401 and Rule ART-302",
        "clue": "Conservation staff access card CONSV-408 and Private Vault cloakroom token C-408 recovered from Locker 14, matching Dr. Julian Vance and modern acrylic forgery RM-1887-04",
    }
    result = evaluate_verdict(
        final_verdict=verdict,
        ground_truth=sample_case.ground_truth.model_dump(),
        was_clean_json=True,
    )
    # Pure merit score: 40 + 25 + 20 + 15 = 100 pts without penalty deductions
    assert result["total_score"] == 100
    assert result["breakdown"]["guardrail_status"]["enforced"] is True


# -------------------------------------------------------------
# 3. Individual Node Execution Tests
# -------------------------------------------------------------

def test_node_1_extractor(sample_case):
    mock_llm = FakeListChatModel(responses=["Fact 1: Rain started at 8:00 PM. Fact 2: Tea served at 8:00 PM."])
    state: GameState = {
        "case_file": sample_case.noisy_case_file,
        "user_1_prompt": "Extract only times and facts.",
    }
    output = agent_1_extractor(state, llm=mock_llm)
    assert "agent_1_output" in output
    assert "Fact 1: Rain started" in output["agent_1_output"]


def test_node_1_extractor_shuffles_events_non_chronological(sample_case):
    from backend.app.graph.guardrails import parse_first_timestamp, is_chronological

    chronological_response = (
        "Evidence extracted:\n"
        "- 08:14: Daniel Kim check-in\n"
        "- 08:16: Malik keycard swipe\n"
        "- 08:30: Gate B07 boarding\n"
        "- 08:47: Door B-Staff-03 swipe\n"
        "- 08:49: Nair logs decoy bag\n"
        "- 09:02: Malik puts bag into Cart MC-08"
    )
    mock_llm = FakeListChatModel(responses=[chronological_response])
    state: GameState = {
        "case_file": sample_case.noisy_case_file,
        "user_1_prompt": "Extract all evidence.",
    }
    output = agent_1_extractor(state, llm=mock_llm)
    out_text = output["agent_1_output"]
    lines = [l for l in out_text.splitlines() if parse_first_timestamp(l) is not None]
    assert len(lines) >= 4
    assert not is_chronological(lines), "Expected Agent 1 output events to be shuffled and non-chronological"


def test_node_1_extractor_guardrail_sanitizes_premature_solving(sample_case):
    # LLM accidentally tries to name the culprit in Step 1
    mock_llm = FakeListChatModel(responses=["Facts: Breaker tripped. The culprit is Dr. Julian Vance who stole the painting."])
    state: GameState = {
        "case_file": sample_case.noisy_case_file,
        "user_1_prompt": "Who did it?",
        "ground_truth": sample_case.ground_truth.model_dump(),
    }
    output = agent_1_extractor(state, llm=mock_llm)
    assert "The culprit is Dr. Julian Vance" not in output["agent_1_output"]


def test_node_2_reconstructor_safe(sample_case):
    mock_llm = FakeListChatModel(responses=["8:00 PM - Tea served. 8:30 PM - Lights flickered. 9:15 PM - Body found."])
    state: GameState = {
        "agent_1_output": "8:00 PM tea, 8:30 PM storm, 9:15 PM body found.",
        "user_2_prompt": "Order chronologically.",
        "ground_truth": sample_case.ground_truth.model_dump(),
        "leak_keywords": sample_case.leak_keywords,
    }
    output = agent_2_reconstructor(state, llm=mock_llm)
    assert "8:00 PM" in output["agent_2_output"]


def test_node_2_reconstructor_guardrail_sanitizes_accusation(sample_case):
    # LLM accidentally includes an accusation in Step 2
    mock_llm = FakeListChatModel(responses=["23:40 blackout occurred. The thief is Dr. Julian Vance who stole the painting."])
    state: GameState = {
        "agent_1_output": "21:15 gala began, 23:40 blackout.",
        "user_2_prompt": "Build timeline.",
        "ground_truth": sample_case.ground_truth.model_dump(),
        "leak_keywords": sample_case.leak_keywords,
    }
    output = agent_2_reconstructor(state, llm=mock_llm)
    # Guardrail ensures the accusation is scrubbed before reaching Player 3
    assert "The thief is Dr. Julian Vance" not in output["agent_2_output"]


def test_node_3_detective(sample_case):
    json_response = '{"culprit": "Dr. Julian Vance", "method": "Breaker blackout", "clue": "Locker 14"}'
    mock_llm = FakeListChatModel(responses=[json_response])
    state: GameState = {
        "agent_2_output": "Timeline of events...",
        "user_3_prompt": "Who did it? Output JSON.",
    }
    output = agent_3_detective(state, llm=mock_llm)
    assert output["final_verdict"]["culprit"] == "Dr. Julian Vance"
    assert output["_was_clean_json"] is True


# -------------------------------------------------------------
# 4. End-to-End LangGraph Workflow Execution
# -------------------------------------------------------------

def test_full_relay_graph_execution(sample_case):
    step1_response = "Fact 1: Breaker B-04 tripped at 23:40:42. Fact 2: Locker 14 in basement."
    step2_response = "Timeline: 21:15 gala began. 23:40 blackout. 23:48 locker search."
    step3_response = '{"culprit": "Dr. Julian Vance", "method": "Breaker B-04 intentional blackout exploiting 90-second auxiliary power failover to swap original canvas with synthetic acrylic forgery and drop tube at Locker 14 under Rule SEC-401 and Rule ART-302", "clue": "Conservation staff access card CONSV-408 and Private Vault cloakroom token C-408 recovered from Locker 14, matching Dr. Julian Vance (Badge CONSV-04 / Conservation), Thorne\'s sub-station sabotage alibi contradiction, and modern acrylic forgery RM-1887-04"}'

    mock_llm = FakeListChatModel(responses=[step1_response, step2_response, step3_response])
    graph = create_relay_graph(llm=mock_llm)

    initial_state: GameState = {
        "session_id": "session_test_001",
        "team_name": "Team Enigma",
        "case_id": sample_case.case_id,
        "case_file": sample_case.noisy_case_file,
        "ground_truth": sample_case.ground_truth.model_dump(),
        "leak_keywords": sample_case.leak_keywords,
        "user_1_prompt": "Role: Evidence Extractor. Identify key people, times, locations, and movements. Distinguish confirmed facts from uncertain information and filter irrelevant noise. Do not infer causes or actions.",
        "user_2_prompt": "Role: Incident Reconstructor. Organize events in chronological sequence of what happened first and next. Connect relevant people, locations, and movements. Identify key dependencies while keeping uncertain relations separate.",
        "user_3_prompt": "Role: Decision Solver. Analyze the reconstructed timeline and operational rules to determine the valid operational action. Identify supporting rules, blocking condition, and resume condition. Output strict JSON with keys: culprit, method, clue.",
    }

    final_state = graph.invoke(initial_state)

    # Verify all stages executed in order
    assert "agent_1_output" in final_state
    assert "agent_2_output" in final_state
    assert "final_verdict" in final_state
    assert "evaluation" in final_state

    # Verify final evaluation
    eval_result = final_state["evaluation"]
    assert eval_result["total_score"] == 100
    assert eval_result["grade"] == "Master Detective (S)"
    assert eval_result["breakdown"]["culprit"]["status"] == "correct"
    assert eval_result["breakdown"]["guardrail_status"]["enforced"] is True


def test_extract_text_content_handling():
    from backend.app.graph.nodes import extract_text_content

    # String input
    assert extract_text_content("hello world") == "hello world"

    # List of text blocks (Gemini style)
    blocks = [{"type": "text", "text": "Extracted clue 1"}, {"type": "text", "text": "Extracted clue 2"}]
    assert extract_text_content(blocks) == "Extracted clue 1\nExtracted clue 2"

    # List of strings
    assert extract_text_content(["line 1", "line 2"]) == "line 1\nline 2"


def test_node_1_with_list_content_response(sample_case):
    class FakeGeminiResponse:
        def __init__(self, content):
            self.content = content

    class FakeGeminiModel:
        def invoke(self, *args, **kwargs):
            return FakeGeminiResponse([{"type": "text", "text": "Fact 1: Boots had mud."}])

    state: GameState = {
        "case_file": sample_case.noisy_case_file,
        "user_1_prompt": "Extract facts.",
    }
    output = agent_1_extractor(state, llm=FakeGeminiModel())
    assert isinstance(output["agent_1_output"], str)
    assert output["agent_1_output"] == "Fact 1: Boots had mud."


def test_evaluator_weak_prompt_verdict(sample_case):
    """Weak prompt leaves fields undetermined, resulting in 0 points and grade F."""
    verdict = {
        "culprit": "Undetermined (Incomplete: User prompt lacked deductive instructions)",
        "method": "Unspecified (Incomplete: Weapon analysis was not requested)",
        "clue": "Unspecified (Incomplete: Smoking gun clue was not requested)",
    }
    result = evaluate_verdict(
        final_verdict=verdict,
        ground_truth=sample_case.ground_truth.model_dump(),
        was_clean_json=True,
    )
    assert result["total_score"] == 0
    assert result["grade"] == "Unsolved (F)"
    assert result["breakdown"]["culprit"]["status"] == "missing"
    assert result["breakdown"]["method"]["status"] == "missing"
    assert result["breakdown"]["clue"]["status"] == "missing"
    assert result["breakdown"]["format"]["status"] == "failed"


def test_evaluator_moderate_prompt_verdict(sample_case):
    """Moderate prompt identifies culprit and broad method, but misses specific mechanism and decisive clue."""
    verdict = {
        "culprit": "Dr. Julian Vance",
        "method": "Breaker blackout",
        "clue": "Present in museum",
    }
    result = evaluate_verdict(
        final_verdict=verdict,
        ground_truth=sample_case.ground_truth.model_dump(),
        was_clean_json=True,
    )
    assert result["total_score"] >= 55
    assert result["breakdown"]["culprit"]["status"] == "correct"
    assert result["breakdown"]["culprit"]["points"] == 40
    assert result["breakdown"]["format"]["status"] == "compliant"


def test_evaluator_unspecified_narrative_does_not_reject_verdict(sample_case):
    """Verifies that natural language containing 'unspecified' in narrative fields does not falsely reject the match."""
    verdict = {
        "culprit": "Dr. Julian Vance",
        "method": "Breaker B-04 intentional blackout exploiting 90-second auxiliary power failover to swap original canvas with synthetic acrylic forgery and drop tube at Locker 14.",
        "motive": "Unspecified financial or personal gain leading to illicit export of the painting.",
        "rule_broken": "Rule SEC-401 & Rule ART-302",
    }
    result = evaluate_verdict(
        final_verdict=verdict,
        ground_truth=sample_case.ground_truth.model_dump(),
        user_1_prompt="Role: Extractor. Extract people Julian Vance, time 21:15, location gallery.",
        agent_1_output="Extracted facts: Julian Vance present at 21:15 in gallery.",
        user_2_prompt="Role: Reconstructor. First Julian Vance attended gala, next blackout occurred at 23:40.",
        agent_2_output="Timeline: 21:15 gala began. 23:40 blackout. 23:48 locker search.",
        user_3_prompt="Analyze rules and output culprit, method, clue in json format.",
        agent_3_output=json.dumps(verdict),
        was_clean_json=True,
    )
    assert result["total_score"] > 50
    assert result["breakdown"]["case_accuracy"]["score"] >= 30
    assert result["breakdown"]["culprit"]["status"] == "correct"
    assert result["breakdown"]["culprit"]["points"] == 15
    assert result["breakdown"]["method"]["status"] == "correct"
    assert result["breakdown"]["method"]["points"] == 15
    assert result["breakdown"]["format"]["status"] == "compliant"


def test_evaluator_incorrect_verdict_preserves_prompt_scores(sample_case):
    """Verifies that an incorrect final verdict does not wipe player prompt engineering points to 0."""
    wrong_verdict = {
        "culprit": "Officer J. Carter",
        "method": "Left gate unlocked during perimeter patrol",
        "clue": "Dropped patrol keys by fire escape",
    }
    result = evaluate_verdict(
        final_verdict=wrong_verdict,
        ground_truth=sample_case.ground_truth.model_dump(),
        user_1_prompt="Role: Extractor. Extract people Julian Vance, time 21:15, location gallery.",
        agent_1_output="Extracted facts: Julian Vance present at 21:15 in gallery.",
        user_2_prompt="Role: Reconstructor. First Julian Vance attended gala, next blackout occurred at 23:40.",
        agent_2_output="Timeline: 21:15 gala began. 23:40 blackout. 23:48 locker search.",
        user_3_prompt="Analyze rules and output culprit, method, clue in json format.",
        agent_3_output=json.dumps(wrong_verdict),
        was_clean_json=True,
    )
    p_sum = (
        result["breakdown"]["player_1"]["score"]
        + result["breakdown"]["player_2"]["score"]
        + result["breakdown"]["player_3"]["score"]
    )
    assert p_sum > 0
    assert result["total_score"] == p_sum + result["breakdown"]["case_accuracy"]["score"]
    assert result["total_score"] > 0


