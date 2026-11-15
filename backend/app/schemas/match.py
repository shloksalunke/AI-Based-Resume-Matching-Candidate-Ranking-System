from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict


class MatchResultResponse(BaseModel):
    id: int
    job_id: int
    resume_id: int
    overall_score: float
    score_breakdown: Dict[str, Any] = {}
    matched_skills: List[str] = []
    partially_matched_skills: List[str] = []
    missing_skills: List[str] = []
    reasons: List[str] = []
    ai_summary: Optional[Dict[str, Any]] = None
    llm_score: Optional[float] = None
    llm_analysis: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class JobMatchRankedItem(BaseModel):
    match_id: int
    resume_id: int
    filename: str
    name: Optional[str] = None
    email: Optional[str] = None
    total_experience_years: float = 0.0
    overall_score: float
    score_breakdown: Dict[str, Any] = {}
    matched_skills: List[str] = []
    partially_matched_skills: List[str] = []
    missing_skills: List[str] = []
    rank: int
    llm_score: Optional[float] = None
    llm_analysis: Optional[Dict[str, Any]] = None


class CandidateDetailedInfo(BaseModel):
    resume_id: int
    filename: str
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    skills: List[str] = []
    total_experience_years: float = 0.0
    companies_and_designations: List[Dict[str, Any]] = []
    education: List[Dict[str, Any]] = []
    certifications: List[str] = []
    projects: List[Dict[str, Any]] = []


class JobDetailedInfo(BaseModel):
    job_id: int
    title: str
    min_experience: float
    required_skills: List[str] = []
    core_skills: List[str] = []
    preferred_skills: List[str] = []
    education: List[str] = []


class JobMatchDetailedResponse(BaseModel):
    match_id: int
    overall_score: float
    score_breakdown: Dict[str, Any]
    matched_skills: List[str] = []
    partially_matched_skills: List[str] = []
    missing_skills: List[str] = []
    reasons: List[str] = []
    ai_summary: Optional[Dict[str, Any]] = None
    llm_score: Optional[float] = None
    llm_analysis: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    candidate: CandidateDetailedInfo
    job: JobDetailedInfo
