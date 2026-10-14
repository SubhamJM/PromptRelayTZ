from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from backend.app.models.evaluator import EvaluationReport
from backend.app.models.scenario import Scenario, ScenarioSummary
from backend.app.models.session import TurnStep


class StartGameRequest(BaseModel):
    team_name: str = Field(..., min_length=1, description="3-person team name")
    scenario_id: Optional[str] = Field(default=None, description="Optional chosen scenario ID")
    case_id: Optional[str] = Field(default=None, description="Alias for scenario_id")


class StartGameResponse(BaseModel):
    session_id: str
    team_name: str
    current_step: TurnStep
    scenario: Optional[Any] = None
    case_id: Optional[str] = None
    case_title: Optional[str] = None
    case_file: Optional[str] = None
    theme: Optional[str] = None
    images: List[Any] = Field(default_factory=list)
    operational_rules: List[str] = Field(default_factory=list)


class Step1Request(BaseModel):
    session_id: str
    prompt: Optional[str] = None
    user_1_prompt: Optional[str] = None


class Step1Response(BaseModel):
    session_id: str
    current_step: TurnStep
    a1_output: str
    agent_1_output: Optional[str] = None


class Step2Request(BaseModel):
    session_id: str
    prompt: Optional[str] = None
    user_2_prompt: Optional[str] = None


class Step2Response(BaseModel):
    session_id: str
    current_step: TurnStep
    a2_output: str
    agent_2_output: Optional[str] = None
    leak_detected: bool = False
    leak_keywords_found: List[str] = []


class Step3Request(BaseModel):
    session_id: str
    prompt: Optional[str] = None
    user_3_prompt: Optional[str] = None


class Step3Response(BaseModel):
    session_id: str
    current_step: TurnStep
    final_verdict: Dict[str, Any]
    evaluation: Any
    agent_3_output: Optional[str] = None
    raw_agent_3_output: Optional[str] = None
    p1_prompt: Optional[str] = None
    a1_output: Optional[str] = None
    p2_prompt: Optional[str] = None
    a2_output: Optional[str] = None
    p3_prompt: Optional[str] = None
    total_score: Optional[int] = None
    grade: Optional[str] = None


class ActiveSessionRecoveryResponse(BaseModel):
    session_id: str
    team_name: str
    scenario: Optional[Any] = None
    case_id: Optional[str] = None
    current_step: TurnStep
    p1_prompt: Optional[str] = None
    a1_output: Optional[str] = None
    p2_prompt: Optional[str] = None
    a2_output: Optional[str] = None
    p3_prompt: Optional[str] = None
    final_verdict: Optional[Dict[str, Any]] = None
    evaluation: Optional[Any] = None
    total_score: Optional[int] = None
    grade: Optional[str] = None
