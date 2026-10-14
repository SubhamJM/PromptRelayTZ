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
    return loader.get_case("case_01_blackwood_manor")


# -------------------------------------------------------------
# 1. JSON Parser Tests
# -------------------------------------------------------------

def test_parse_json_verdict_clean():
    raw = '{"culprit": "Dr. Arthur Bell", "method": "Potassium cyanide", "clue": "Sugar tongs"}'
    parsed, was_clean = parse_json_verdict(raw)
    assert was_clean is True
    assert parsed["culprit"] == "Dr. Arthur Bell"
    assert parsed["method"] == "Potassium cyanide"
    assert parsed["clue"] == "Sugar tongs"


def test_parse_json_verdict_markdown_fenced():
    raw = '```json\n{"culprit": "Dr. Arthur Bell", "method": "Cyanide in sugar", "clue": "Muddy boots"}\n```'
    parsed, was_clean = parse_json_verdict(raw)
    assert was_clean is True
    assert parsed["culprit"] == "Dr. Arthur Bell"


def test_parse_json_verdict_conversational_wrapper():
    raw = 'Based on the timeline, here is my verdict:\n{"culprit": "Dr. Arthur Bell", "method": "Cyanide", "clue": "Muddy boots"}\nLet me know if you need more details.'
    parsed, was_clean = parse_json_verdict(raw)
    assert was_clean is False  # Had outside conversational text
    assert parsed["culprit"] == "Dr. Arthur Bell"
    assert parsed["method"] == "Cyanide"


def test_parse_json_verdict_broken():
    raw = "The killer is definitely Charles because he had the motive!"
    parsed, was_clean = parse_json_verdict(raw)
    assert was_clean is False
    assert parsed["culprit"] == ""


# -------------------------------------------------------------
# 2. Analytical Evaluator Tests
# -------------------------------------------------------------

def test_evaluator_perfect_score(sample_case):
    verdict = {
        "culprit": "Dr. Arthur Bell",
        "method": "Potassium cyanide in sugar cubes using silver sugar tongs",
        "clue": "Dr. Bell's muddy boots from the greenhouse path and cyanide on tongs",
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
        "culprit": "Charles Blackwood",
        "method": "Poisoned tea",
        "clue": "Threatening letter in violet ink",
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
        "culprit": "Dr. Arthur Bell",
        "method": "Cyanide poison",
        "clue": "Muddy boots and tongs",
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


def test_node_1_extractor_guardrail_sanitizes_premature_solving(sample_case):
    # LLM accidentally tries to name the culprit in Step 1
    mock_llm = FakeListChatModel(responses=["Facts: Tea was served. The killer is Dr. Arthur Bell who is guilty."])
    state: GameState = {
        "case_file": sample_case.noisy_case_file,
        "user_1_prompt": "Who did it?",
        "ground_truth": sample_case.ground_truth.model_dump(),
    }
    output = agent_1_extractor(state, llm=mock_llm)
    assert "The killer is Dr. Arthur Bell" not in output["agent_1_output"]


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
    mock_llm = FakeListChatModel(responses=["8:00 PM tea served. The killer is Dr. Arthur Bell who poisoned Reginald."])
    state: GameState = {
        "agent_1_output": "8:00 PM tea, 9:05 PM doctor arrived.",
        "user_2_prompt": "Build timeline.",
        "ground_truth": sample_case.ground_truth.model_dump(),
        "leak_keywords": sample_case.leak_keywords,
    }
    output = agent_2_reconstructor(state, llm=mock_llm)
    # Guardrail ensures the accusation is scrubbed before reaching Player 3
    assert "The killer is Dr. Arthur Bell" not in output["agent_2_output"]


def test_node_3_detective(sample_case):
    json_response = '{"culprit": "Dr. Arthur Bell", "method": "Cyanide", "clue": "Muddy boots"}'
    mock_llm = FakeListChatModel(responses=[json_response])
    state: GameState = {
        "agent_2_output": "Timeline of events...",
        "user_3_prompt": "Who did it? Output JSON.",
    }
    output = agent_3_detective(state, llm=mock_llm)
    assert output["final_verdict"]["culprit"] == "Dr. Arthur Bell"
    assert output["_was_clean_json"] is True


# -------------------------------------------------------------
# 4. End-to-End LangGraph Workflow Execution
# -------------------------------------------------------------

def test_full_relay_graph_execution(sample_case):
    step1_response = "Fact 1: Tea served with sugar. Fact 2: Mud on boots. Fact 3: Charity audit document."
    step2_response = "Timeline: 8:00 PM tea served. 8:35 PM footsteps. 9:05 PM guest arrived."
    step3_response = '{"culprit": "Dr. Arthur Bell", "method": "Potassium cyanide in sugar cubes", "clue": "Muddy boots from greenhouse path and cyanide on sugar tongs"}'

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
        "culprit": "Dr. Arthur Bell",
        "method": "Poisoning",
        "clue": "Present in the manor",
    }
    result = evaluate_verdict(
        final_verdict=verdict,
        ground_truth=sample_case.ground_truth.model_dump(),
        was_clean_json=True,
    )
    # Culprit = 40, Method (partial) = 15, Clue (generic/missed) = 0, Format = 15 -> 70 pts
    assert result["total_score"] >= 55
    assert result["breakdown"]["culprit"]["status"] == "correct"
    assert result["breakdown"]["culprit"]["points"] == 40
    assert result["breakdown"]["format"]["status"] == "compliant"

