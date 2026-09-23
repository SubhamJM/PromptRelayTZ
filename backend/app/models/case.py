from typing import List, Optional
from pydantic import BaseModel, Field


class GroundTruth(BaseModel):
    """Ground truth answer key for a murder mystery case."""
    culprit: str = Field(..., description="Full name of the true murderer")
    weapon_or_method: str = Field(..., description="Method or weapon used in the murder")
    key_clue: str = Field(..., description="The definitive smoking gun clue")
    motive: str = Field(..., description="The underlying motive for the crime")
    suspects: List[str] = Field(default_factory=list, description="List of all suspects introduced in the case")


class CaseModel(BaseModel):
    """Schema representing a complete murder mystery case file."""
    case_id: str = Field(..., description="Unique alphanumeric identifier (e.g. case_01_blackwood_manor)")
    title: str = Field(..., description="Engaging public title of the case")
    difficulty: str = Field(default="Medium", description="Estimated difficulty: Easy, Medium, or Hard")
    synopsis: str = Field(..., description="1-2 sentence overview for the MC / event host")
    noisy_case_file: str = Field(
        ...,
        description="The unformatted, chaotic case notes containing genuine clues, red herrings, and dialogue"
    )
    ground_truth: GroundTruth = Field(..., description="Verified solution key")
    leak_keywords: List[str] = Field(
        default_factory=list,
        description="Keywords/phrases that flag a leak trap violation if mentioned early (e.g., culprit's name, weapon)"
    )
    decoy_clues: List[str] = Field(
        default_factory=list,
        description="List of prominent red herrings in the noisy text to aid evaluation"
    )
