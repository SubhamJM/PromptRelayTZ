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
    assert result["breakdown"]["leak_penalty"]["applied"] is False


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


def test_evaluator_leak_penalty(sample_case):
    verdict = {
        "culprit": "Dr. Arthur Bell",
        "method": "Cyanide poison",
        "clue": "Muddy boots and tongs",
    }
    result = evaluate_verdict(
        final_verdict=verdict,
        ground_truth=sample_case.ground_truth.model_dump(),
        leak_detected=True,  # Step 2 leaked the culprit
        was_clean_json=True,
    )
    assert result["breakdown"]["leak_penalty"]["applied"] is True
    assert result["breakdown"]["leak_penalty"]["penalty"] == 20
    # Score without penalty would be 100, with penalty is 80
    assert result["total_score"] == 80


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


def test_node_2_reconstructor_safe(sample_case):
    mock_llm = FakeListChatModel(responses=["8:00 PM - Tea served. 8:30 PM - Lights flickered. 9:15 PM - Body found."])
    state: GameState = {
        "agent_1_output": "8:00 PM tea, 8:30 PM storm, 9:15 PM body found.",
        "user_2_prompt": "Order chronologically.",
        "ground_truth": sample_case.ground_truth.model_dump(),
        "leak_keywords": sample_case.leak_keywords,
    }
    output = agent_2_reconstructor(state, llm=mock_llm)
    assert output["leak_detected"] is False
    assert len(output["leak_keywords_found"]) == 0
    assert "8:00 PM" in output["agent_2_output"]


def test_node_2_reconstructor_leak_trap(sample_case):
    # LLM accidentally names Dr. Arthur Bell
    mock_llm = FakeListChatModel(responses=["8:00 PM tea served. 9:05 PM Dr. Arthur Bell arrived with muddy boots."])
    state: GameState = {
        "agent_1_output": "8:00 PM tea, 9:05 PM doctor arrived.",
        "user_2_prompt": "Build timeline.",
        "ground_truth": sample_case.ground_truth.model_dump(),
        "leak_keywords": sample_case.leak_keywords,
    }
    output = agent_2_reconstructor(state, llm=mock_llm)
    assert output["leak_detected"] is True
    assert any("Bell" in kw for kw in output["leak_keywords_found"])


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
        "user_1_prompt": "Extract facts.",
        "user_2_prompt": "Build chronological timeline without accusing anyone.",
        "user_3_prompt": "Identify the killer and output strictly JSON.",
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
    assert eval_result["breakdown"]["leak_penalty"]["applied"] is False
