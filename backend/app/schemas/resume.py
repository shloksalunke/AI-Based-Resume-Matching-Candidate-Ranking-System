from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class ResumeBase(BaseModel):
    filename: str
    raw_text: str


class ResumeResponse(ResumeBase):
    id: int
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    skills: List[str] = []
    total_experience_years: float = 0.0
    companies_and_designations: List[Dict[str, Any]] = []
    education: List[Dict[str, Any]] = []
    certifications: List[str] = []
    projects: List[Dict[str, Any]] = []
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ResumeUploadResult(BaseModel):
    filename: str
    status: str  # "success" or "error"
    resume_id: Optional[int] = None
    candidate_name: Optional[str] = None
    error_message: Optional[str] = None


class ResumeUploadBatchResponse(BaseModel):
    total: int
    successful: int
    failed: int
    results: List[ResumeUploadResult]
