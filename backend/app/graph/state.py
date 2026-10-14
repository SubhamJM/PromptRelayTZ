from typing import Any, Dict, List, Optional, TypedDict
from backend.app.models.scenario import Scenario
from backend.app.models.evaluator import EvaluationReport


class RelayState(TypedDict, total=False):
    session_id: str
    scenario: Scenario
    team_name: str

    # Turn 1
    p1_prompt: str
    a1_output: str

    # Turn 2
    p2_prompt: str
    a2_output: str

    # Turn 3
    p3_prompt: str
    a3_raw_output: str
    final_verdict: Dict[str, Any]

    # Evaluation
    evaluation: Optional[Any]

    # Legacy GameState fields
    case_id: str
    case_file: str
    ground_truth: Dict[str, Any]
    leak_keywords: List[str]
    user_1_prompt: str
    agent_1_output: str
    user_2_prompt: str
    agent_2_output: str
    user_3_prompt: str
    agent_3_output: str
    raw_agent_3_output: str
    _was_clean_json: bool
    leak_detected: bool
    leak_keywords_found: List[str]

    # Diagnostics
    error: Optional[str]


GameState = RelayState
