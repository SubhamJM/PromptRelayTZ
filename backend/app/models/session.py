from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, model_validator

from backend.app.models.evaluator import EvaluationReport
from backend.app.models.scenario import Scenario


class TurnStep(str, Enum):
    WELCOME = "welcome"
    STEP1 = "step1"
    HANDOFF1 = "handoff1"
    STEP2 = "step2"
    HANDOFF2 = "handoff2"
    STEP3 = "step3"
    COMPLETED = "completed"


class GameSession(BaseModel):
    session_id: str
    team_name: str
    scenario_id: Optional[str] = None
    scenario: Optional[Scenario] = None
    current_step: TurnStep = TurnStep.STEP1

    @model_validator(mode="before")
    @classmethod
    def _coerce_scenario(cls, data: Any) -> Any:
        if isinstance(data, dict):
            sc = data.get("scenario")
            if isinstance(sc, dict):
                try:
                    data["scenario"] = Scenario.model_validate(sc)
                except Exception:
                    pass
            elif not sc and data.get("scenario_id"):
                try:
                    from backend.app.services.scenario_loader import ScenarioLoader
                    loaded = ScenarioLoader().get(data["scenario_id"])
                    if loaded:
                        data["scenario"] = loaded
                except Exception:
                    pass
        return data

    # Turn 1
    p1_prompt: Optional[str] = None
    a1_output: Optional[str] = None

    # Turn 2
    p2_prompt: Optional[str] = None
    a2_output: Optional[str] = None

    # Turn 3
    p3_prompt: Optional[str] = None
    a3_raw_output: Optional[str] = None
    final_verdict: Optional[Dict[str, Any]] = None

    # Evaluation
    evaluation: Optional[Any] = None

    # Backward compatibility with legacy test helpers
    case: Optional[Any] = None
    case_id: Optional[str] = None
    state: Optional[Dict[str, Any]] = None

    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class SessionResponse(BaseModel):
    session_id: str
    team_name: str
    scenario_id: str
    scenario_title: str
    scenario_type: str
    current_step: TurnStep
    created_at: str
    updated_at: str
