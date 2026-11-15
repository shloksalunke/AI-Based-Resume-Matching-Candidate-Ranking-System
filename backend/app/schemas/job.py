from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class JobDescriptionBase(BaseModel):
    title: str = Field(..., min_length=2, max_length=255)
    raw_text: str = Field(..., min_length=10)


class JobDescriptionCreate(JobDescriptionBase):
    pass


class JobDescriptionResponse(JobDescriptionBase):
    id: int
    required_skills: List[str] = []
    core_skills: List[str] = []
    preferred_skills: List[str] = []
    min_experience: float = 0.0
    education: List[str] = []
    keywords: List[str] = []
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
