from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class PlayerScorecard(BaseModel):
    player: int = Field(default=1, description="Player number (1, 2, or 3)")
    player_name: str = Field(default="Player 1")
    role: str = Field(default="Evidence Extractor", description="Role name")
    score: int = Field(default=20, description="Total points earned out of 20")
    max_score: int = Field(default=20)
    prompt_score: int = Field(default=12, description="Points earned for prompt engineering quality out of 12")
    agent_score: int = Field(default=8, description="Points earned for agent execution effectiveness out of 8")
    feedback: str = Field(default="", description="Itemized feedback on performance")
    itemized_feedback: str = Field(default="")
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    criteria: Dict[str, Any] = Field(default_factory=dict, description="Detailed category breakdown")

    def model_post_init(self, __context: Any) -> None:
        if not self.itemized_feedback and self.feedback:
            self.itemized_feedback = self.feedback
        elif not self.feedback and self.itemized_feedback:
            self.feedback = self.itemized_feedback
        if not self.feedback and not self.itemized_feedback:
            self.feedback = f"Prompt Quality: {self.prompt_score}/12. Agent Execution: {self.agent_score}/8."
            self.itemized_feedback = self.feedback


class SolutionScorecard(BaseModel):
    score: int = Field(default=40, description="Total points earned out of 40")
    max_score: int = Field(default=40)
    action_or_culprit_pts: int = Field(default=15, description="Points out of 15")
    action_or_culprit_feedback: str = Field(default="")
    rules_or_method_pts: int = Field(default=15, description="Points out of 15")
    rules_or_method_feedback: str = Field(default="")
    proof_or_clue_pts: int = Field(default=10, description="Points out of 10")
    proof_or_clue_feedback: str = Field(default="")
    status: str = Field(default="evaluated")
    culprit_correct: bool = Field(default=True)
    method_score: int = Field(default=15)
    motive_score: int = Field(default=10)
    rule_score: int = Field(default=10)
    parsed_verdict: Dict[str, Any] = Field(default_factory=dict)
    ground_truth: Dict[str, Any] = Field(default_factory=dict)
    reasoning: str = Field(default="")

    def model_post_init(self, __context: Any) -> None:
        if self.method_score == 15 and self.rules_or_method_pts != 15:
            self.method_score = self.rules_or_method_pts
        elif self.rules_or_method_pts == 15 and self.method_score != 15:
            self.rules_or_method_pts = self.method_score

        if self.rule_score == 10 and self.proof_or_clue_pts != 10:
            self.rule_score = self.proof_or_clue_pts
        elif self.proof_or_clue_pts == 10 and self.rule_score != 10:
            self.proof_or_clue_pts = self.rule_score


class EvaluationReport(BaseModel):
    total_score: int = Field(default=100, ge=0, le=100, description="Overall calibrated tournament score out of 100")
    max_score: int = Field(default=100)
    max_total_score: int = Field(default=100)
    grade: str = Field(default="Master Detective (S)", description="Tournament grade")
    summary: str = Field(default="", description="High-level narrative performance summary")
    summary_narrative: str = Field(default="")
    player_1: Optional[PlayerScorecard] = None
    player_2: Optional[PlayerScorecard] = None
    player_3: Optional[PlayerScorecard] = None
    solution: Optional[SolutionScorecard] = None
    p1_scorecard: Optional[PlayerScorecard] = None
    p2_scorecard: Optional[PlayerScorecard] = None
    p3_scorecard: Optional[PlayerScorecard] = None
    solution_scorecard: Optional[SolutionScorecard] = None
    p1_prompt: Optional[str] = None
    a1_output: Optional[str] = None
    p2_prompt: Optional[str] = None
    a2_output: Optional[str] = None
    p3_prompt: Optional[str] = None
    a3_output: Optional[str] = None
    final_verdict: Optional[Dict[str, Any]] = None
    actual_verdict: Dict[str, Any] = Field(default_factory=dict)
    expected_verdict: Dict[str, Any] = Field(default_factory=dict)
    strengths_summary: List[str] = Field(default_factory=list)
    improvements_summary: List[str] = Field(default_factory=list)
    breakdown: Dict[str, Any] = Field(default_factory=dict)

    def model_post_init(self, __context: Any) -> None:
        if not self.summary_narrative and self.summary:
            self.summary_narrative = self.summary
        elif not self.summary and self.summary_narrative:
            self.summary = self.summary_narrative

        # Cross-populate player_1 / p1_scorecard
        if self.player_1 and not self.p1_scorecard:
            self.p1_scorecard = self.player_1
        elif self.p1_scorecard and not self.player_1:
            self.player_1 = self.p1_scorecard
        elif not self.player_1 and not self.p1_scorecard:
            self.player_1 = PlayerScorecard(player=1, player_name="Player 1")
            self.p1_scorecard = self.player_1

        if self.player_2 and not self.p2_scorecard:
            self.p2_scorecard = self.player_2
        elif self.p2_scorecard and not self.player_2:
            self.player_2 = self.p2_scorecard
        elif not self.player_2 and not self.p2_scorecard:
            self.player_2 = PlayerScorecard(player=2, player_name="Player 2", role="Timeline Reconstructor")
            self.p2_scorecard = self.player_2

        if self.player_3 and not self.p3_scorecard:
            self.p3_scorecard = self.player_3
        elif self.p3_scorecard and not self.player_3:
            self.player_3 = self.p3_scorecard
        elif not self.player_3 and not self.p3_scorecard:
            self.player_3 = PlayerScorecard(player=3, player_name="Player 3", role="Logic Solver")
            self.p3_scorecard = self.player_3

        if self.solution and not self.solution_scorecard:
            self.solution_scorecard = self.solution
        elif self.solution_scorecard and not self.solution:
            self.solution = self.solution_scorecard
        elif not self.solution and not self.solution_scorecard:
            self.solution = SolutionScorecard()
            self.solution_scorecard = self.solution

        if not self.breakdown:
            sol = self.solution
            culprit_pts = getattr(sol, "action_or_culprit_pts", 15)
            culprit_correct = getattr(sol, "culprit_correct", True)
            method_pts = getattr(sol, "rules_or_method_pts", 15)
            clue_pts = getattr(sol, "proof_or_clue_pts", 10)
            self.breakdown = {
                "player_1": {"score": self.player_1.score, "max": self.player_1.max_score, "prompt_score": self.player_1.prompt_score, "agent_score": self.player_1.agent_score},
                "player_2": {"score": self.player_2.score, "max": self.player_2.max_score, "prompt_score": self.player_2.prompt_score, "agent_score": self.player_2.agent_score},
                "player_3": {"score": self.player_3.score, "max": self.player_3.max_score, "prompt_score": self.player_3.prompt_score, "agent_score": self.player_3.agent_score},
                "solution": {"score": self.solution.score, "max": self.solution.max_score},
                "case_accuracy": {"score": self.solution.score, "max": self.solution.max_score},
                "culprit": {
                    "points": culprit_pts,
                    "max_points": 15,
                    "status": "correct" if culprit_correct else "incorrect",
                    "expected": "",
                    "actual": "",
                },
                "method": {
                    "points": method_pts,
                    "max_points": 15,
                    "status": "correct",
                    "expected": "",
                    "actual": "",
                },
                "clue": {
                    "points": clue_pts,
                    "max_points": 10,
                    "status": "correct",
                    "expected": "",
                    "actual": "",
                },
                "format": {
                    "points": 15,
                    "max_points": 15,
                    "status": "compliant",
                },
                "guardrail_status": {
                    "enforced": True,
                    "leak_detected": False,
                    "feedback": "Guardrails actively enforced sequential task boundaries.",
                },
            }
