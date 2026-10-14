from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class GroundTruth(BaseModel):
    """
    Ground truth answer key for an incident or case.
    Supports operational crisis scenarios (action, rules, blocking condition, resume condition)
    and investigative mystery scenarios.
    """
    # Primary Operational Decision Ground Truth (e.g. Airport Security Crisis)
    valid_action: Optional[str] = Field(default=None, description="The required operational action or verdict")
    supporting_rules: List[str] = Field(default_factory=list, description="Operational rules that support the decision")
    blocking_condition: Optional[str] = Field(default=None, description="Condition currently preventing normal operations")
    resume_condition: Optional[str] = Field(default=None, description="Condition required before operations can resume")

    # Investigative / Legacy compatibility fields
    culprit: Optional[str] = Field(default=None, description="Identified perpetrator / responsible party")
    weapon_or_method: Optional[str] = Field(default=None, description="Method or mechanism involved")
    key_clue: Optional[str] = Field(default=None, description="Definitive smoking gun evidence")
    motive: Optional[str] = Field(default=None, description="Underlying motive or root cause")
    suspects: List[str] = Field(default_factory=list, description="List of key persons of interest / suspects")


class CaseModel(BaseModel):
    """Schema representing an incident case dossier."""
    case_id: str = Field(..., description="Unique alphanumeric identifier (e.g. case_airport_crisis_flight_472)")
    title: str = Field(..., description="Engaging public title of the incident/scenario")
    difficulty: str = Field(default="Medium", description="Estimated difficulty: Easy, Medium, or Hard")
    synopsis: str = Field(..., description="Overview for participants and organizers")
    theme: Optional[str] = Field(default="Murder Mystery", description="Theme/genre of the case: 'Airport Crisis' or 'Murder Mystery'")
    images: List[Dict[str, Any]] = Field(default_factory=list, description="List of visual evidence images with src, filename, timestamp")
    noisy_case_file: str = Field(
        ...,
        description="Collection of multi-source visual evidence, CCTV transcripts, gate logs, sensor reports, and noise"
    )
    operational_rules: List[str] = Field(
        default_factory=list,
        description="Airport or regulatory operational safety rules provided to Agent 3"
    )
    ground_truth: GroundTruth = Field(..., description="Verified solution key")
    leak_keywords: List[str] = Field(
        default_factory=list,
        description="Keywords/phrases that flag a leak trap violation if mentioned prematurely"
    )
    decoy_clues: List[str] = Field(
        default_factory=list,
        description="List of prominent irrelevant noise or red herrings"
    )
