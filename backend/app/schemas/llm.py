from typing import Any, List, Optional
from pydantic import BaseModel, Field, field_validator


class CandidateAiSummary(BaseModel):
    summary: str = Field(..., description="Concise 2-3 sentence overview of the candidate's alignment with the role")
    strengths: List[str] = Field(default_factory=list, description="Up to 3 key demonstrated strengths")
    concerns: List[str] = Field(default_factory=list, description="Up to 3 gaps or missing qualifications")
    recommendation: str = Field(default="Possible fit", description="Executive recommendation")

    @field_validator("recommendation", mode="before")
    @classmethod
    def normalize_recommendation(cls, v: Any) -> str:
        s = str(v).strip().lower()
        if "strong" in s:
            return "Strong fit"
        elif "possible" in s or "moderate" in s:
            return "Possible fit"
        return "Weak fit"


class CandidateAiEvaluation(BaseModel):
    ai_score: float = Field(default=0.0, description="Overall AI evaluated score (0-100)")
    matched_skills: List[str] = Field(default_factory=list)
    missing_skills: List[str] = Field(default_factory=list)
    equivalent_skills: List[str] = Field(default_factory=list)
    experience_assessment: str = Field(default="")
    summary: str = Field(default="")
    strengths: List[str] = Field(default_factory=list)
    concerns: List[str] = Field(default_factory=list)
    recommendation: str = Field(default="Possible fit")
    reasons: List[str] = Field(default_factory=list)
    error: Optional[str] = None

    @field_validator("ai_score", mode="before")
    @classmethod
    def clamp_score(cls, v: Any) -> float:
        try:
            val = float(v)
            return round(max(0.0, min(100.0, val)), 1)
        except (ValueError, TypeError):
            return 0.0

    @field_validator("strengths", mode="before")
    @classmethod
    def clamp_strengths(cls, v: Any) -> List[str]:
        if isinstance(v, list):
            return [str(x) for x in v[:3]]
        return []

    @field_validator("concerns", mode="before")
    @classmethod
    def clamp_concerns(cls, v: Any) -> List[str]:
        if isinstance(v, list):
            return [str(x) for x in v[:3]]
        return []

    @field_validator("reasons", mode="before")
    @classmethod
    def clamp_reasons(cls, v: Any) -> List[str]:
        if isinstance(v, list):
            return [str(x) for x in v[:5]]
        return []

    @field_validator("recommendation", mode="before")
    @classmethod
    def normalize_recommendation(cls, v: Any) -> str:
        s = str(v).strip().lower()
        if "strong" in s:
            return "Strong fit"
        elif "possible" in s or "moderate" in s:
            return "Possible fit"
        return "Weak fit"


class LlmStatusResponse(BaseModel):
    enabled: bool
    max_candidates: int
