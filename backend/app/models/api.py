from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from backend.app.models.case import GroundTruth


# -------------------------------------------------------------
# Case Information
# -------------------------------------------------------------

class CaseInfo(BaseModel):
    case_id: str
    title: str
    difficulty: str
    synopsis: str
    theme: Optional[str] = "Murder Mystery"
    images: List[Dict[str, Any]] = Field(default_factory=list)


# -------------------------------------------------------------
# Wizard Request & Response Models
# -------------------------------------------------------------

class StartGameRequest(BaseModel):
    team_name: str = Field(..., min_length=1, description="Name of the 3-person team")
    case_id: Optional[str] = Field(default=None, description="Optional case ID; random if omitted")


class StartGameResponse(BaseModel):
    session_id: str
    team_name: str
    case_id: str
    case_title: str
    case_file: str = Field(..., description="Raw case story displayed ONLY to Player 1")
    theme: Optional[str] = "Murder Mystery"
    images: List[Dict[str, Any]] = Field(default_factory=list)
    operational_rules: List[str] = Field(default_factory=list)


class Step1Request(BaseModel):
    session_id: str
    user_1_prompt: str = Field(..., min_length=1, description="Prompt written by Player 1")


class Step1Response(BaseModel):
    session_id: str
    agent_1_output: str = Field(..., description="Evidence extracted by Agent 1 (displayed to Player 2)")


class Step2Request(BaseModel):
    session_id: str
    user_2_prompt: str = Field(..., min_length=1, description="Prompt written by Player 2")


class Step2Response(BaseModel):
    session_id: str
    agent_2_output: str = Field(..., description="Timeline reconstructed by Agent 2 (displayed to Player 3)")
    leak_detected: bool = Field(..., description="Flagged if culprit name leaked prematurely")


class Step3Request(BaseModel):
    session_id: str
    user_3_prompt: str = Field(..., min_length=1, description="Prompt written by Player 3")


class Step3Response(BaseModel):
    session_id: str
    final_verdict: Dict[str, Any]
    evaluation: Dict[str, Any]
    total_score: int
    grade: str


class SessionStatusResponse(BaseModel):
    session_id: str
    team_name: str
    case_id: str
    case_title: str
    current_step: str  # "step1", "step2", "step3", "completed"
    user_1_prompt: Optional[str] = None
    agent_1_output: Optional[str] = None
    user_2_prompt: Optional[str] = None
    agent_2_output: Optional[str] = None
    user_3_prompt: Optional[str] = None
    final_verdict: Optional[Dict[str, Any]] = None
    evaluation: Optional[Dict[str, Any]] = None
    total_score: Optional[int] = None
    grade: Optional[str] = None
    created_at: str
    updated_at: str


# -------------------------------------------------------------
# Leaderboard Models
# -------------------------------------------------------------

class LeaderboardEntry(BaseModel):
    rank: int
    session_id: str
    team_name: str
    case_id: str
    case_title: str
    total_score: int
    grade: str
    culprit_score: int
    method_score: int
    clue_score: int
    format_score: int
    completed_at: str


class LeaderboardResponse(BaseModel):
    total_matches: int
    leaderboard: List[LeaderboardEntry]


# -------------------------------------------------------------
# Admin & Organizer Models
# -------------------------------------------------------------

class TournamentStatsResponse(BaseModel):
    total_matches: int
    average_score: float
    highest_score: int
    lowest_score: int
    perfect_or_s_count: int
    culprit_solved_count: int
    culprit_solve_rate: float
    most_popular_case: str


class MatchDetailResponse(BaseModel):
    session_id: str
    team_name: str
    case_id: str
    case_title: str
    total_score: int
    grade: str
    culprit_score: int
    method_score: int
    clue_score: int
    format_score: int
    final_verdict: Dict[str, Any]
    evaluation: Dict[str, Any]
    user_1_prompt: Optional[str] = None
    agent_1_output: Optional[str] = None
    user_2_prompt: Optional[str] = None
    agent_2_output: Optional[str] = None
    user_3_prompt: Optional[str] = None
    created_at: str
    completed_at: str


class CaseDetailResponse(BaseModel):
    case_id: str
    title: str
    difficulty: str
    synopsis: str
    leak_keywords: List[str]
    ground_truth: Dict[str, Any]


class CreateCaseRequest(BaseModel):
    case_id: str = Field(..., min_length=3, description="Unique slug for case, e.g. case_04_clockwork_crypt")
    title: str = Field(..., min_length=3)
    difficulty: str = Field(default="Medium", description="Easy, Medium, or Hard")
    synopsis: str = Field(..., min_length=10)
    noisy_case_file: str = Field(..., min_length=50)
    ground_truth: GroundTruth
    leak_keywords: List[str] = Field(default_factory=list)


class ConfigureLLMRequest(BaseModel):
    provider: Optional[str] = Field(default=None, description="'gemini', 'openai', 'anthropic', or 'offline'")
    model_name: Optional[str] = None
    temperature: Optional[float] = None
    timeout_seconds: Optional[int] = None
    fallback_to_offline: Optional[bool] = None


class LLMStatusResponse(BaseModel):
    status: str
    provider: str
    model_name: str
    temperature: float
    timeout_seconds: int
    fallback_to_offline: bool
    latency_ms: Optional[float] = None
    message: Optional[str] = None


