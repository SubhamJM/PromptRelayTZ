from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, model_validator


class ScenarioType(str, Enum):
    IMAGE = "image"
    TEXT = "text"


class EvidenceItem(BaseModel):
    id: str = Field(..., description="Unique evidence identifier, e.g. 'ev_01'")
    title: str = Field(..., description="Display title of the evidence")
    category: str = Field(default="Evidence", description="Category: CCTV Surveillance, Document, Sensor, etc.")
    badge: str = Field(default="", description="Short label badge, e.g. 'CAM 03 • Check-in A'")
    timestamp: Optional[str] = Field(default=None, description="Logged timestamp or date")
    src: Optional[str] = Field(default=None, description="Image path or URL for image-based evidence")
    prompt_hint: str = Field(default="", description="Strategy hint advising what to direct the AI to extract")
    description: str = Field(default="", description="High-level description of what this item captures")
    ocr_ledger: str = Field(
        default="",
        description="High-fidelity textual OCR transcription, metadata, and fine-grained observations"
    )


class GroundTruth(BaseModel):
    target_action_or_culprit: str = Field(default="", description="Expected operational action or primary culprit")
    target_rules_or_method: str = Field(default="", description="Expected supporting rules/protocols or weapon/method")
    target_proof_or_clue: str = Field(default="", description="Expected decisive smoking-gun evidence or blocking condition")
    explanation: str = Field(default="", description="Comprehensive reasoning explaining the ground truth")
    suspects_or_entities: List[str] = Field(default_factory=list, description="List of persons of interest or entities")
    motive_or_hazard: Optional[str] = Field(default=None, description="Underlying motivation or security hazard")

    # Compatibility fields
    culprit: Optional[str] = None
    weapon_or_method: Optional[str] = None
    key_clue: Optional[str] = None
    suspects: List[str] = Field(default_factory=list)
    motive: Optional[str] = None
    valid_action: Optional[str] = None
    supporting_rules: List[str] = Field(default_factory=list)
    blocking_condition: Optional[str] = None
    resume_condition: Optional[str] = None

    def model_post_init(self, __context: Any) -> None:
        if self.target_action_or_culprit:
            if not self.culprit:
                self.culprit = self.target_action_or_culprit
            if not self.valid_action:
                self.valid_action = self.target_action_or_culprit
        elif self.culprit and not self.target_action_or_culprit:
            self.target_action_or_culprit = self.culprit

        if self.target_rules_or_method:
            if not self.weapon_or_method:
                self.weapon_or_method = self.target_rules_or_method
        elif self.weapon_or_method and not self.target_rules_or_method:
            self.target_rules_or_method = self.weapon_or_method

        if self.target_proof_or_clue:
            if not self.key_clue:
                self.key_clue = self.target_proof_or_clue
        elif self.key_clue and not self.target_proof_or_clue:
            self.target_proof_or_clue = self.key_clue

        if self.suspects_or_entities:
            if not self.suspects:
                self.suspects = list(self.suspects_or_entities)
        elif self.suspects and not self.suspects_or_entities:
            self.suspects_or_entities = list(self.suspects)

        if self.motive_or_hazard and not self.motive:
            self.motive = self.motive_or_hazard
        elif self.motive and not self.motive_or_hazard:
            self.motive_or_hazard = self.motive


class Scenario(BaseModel):
    id: str = Field(..., description="Unique scenario slug, e.g. 'scenario_airport_crisis'")
    type: ScenarioType = Field(default=ScenarioType.TEXT, description="'image' for visual evidence, 'text' for dossiers")
    title: str = Field(..., description="Scenario title")
    difficulty: str = Field(default="Medium", description="Difficulty: Easy, Medium, Hard")
    synopsis: str = Field(..., description="Brief synopsis explaining the scenario setup")
    dossier_text: str = Field(..., description="Full narrative briefing and unformatted case file")
    evidence_items: List[EvidenceItem] = Field(default_factory=list, description="Structured items (photos or docs)")
    operational_rules: List[str] = Field(
        default_factory=list,
        description="Operational protocols, safety rules, or legal standards for Agent 3"
    )
    ground_truth: GroundTruth = Field(..., description="Target solution key")
    spoiler_keywords: List[str] = Field(
        default_factory=list,
        description="Keywords strictly sanitized from early agents to prevent leaks"
    )
    leak_keywords: List[str] = Field(
        default_factory=list,
        description="Compatibility alias for spoiler_keywords"
    )
    decoy_items: List[str] = Field(
        default_factory=list,
        description="Prominent peripheral noise or red herrings"
    )
    objective: str = Field(default="", description="Player objective summary")
    rules: List[Any] = Field(default_factory=list, description="Rules list for frontend tabs")

    @model_validator(mode="before")
    @classmethod
    def remap_legacy_case(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "case_id" in data and "id" not in data:
                data["id"] = data["case_id"]
            if "noisy_case_file" in data and "dossier_text" not in data:
                data["dossier_text"] = data["noisy_case_file"]
        return data

    def model_post_init(self, __context: Any) -> None:
        if self.spoiler_keywords and not self.leak_keywords:
            self.leak_keywords = list(self.spoiler_keywords)
        elif self.leak_keywords and not self.spoiler_keywords:
            self.spoiler_keywords = list(self.leak_keywords)
        if not self.objective:
            self.objective = self.synopsis


class ScenarioSummary(BaseModel):
    id: str
    type: ScenarioType
    title: str
    difficulty: str
    synopsis: str
    evidence_count: int
    rule_count: int
    has_images: bool
