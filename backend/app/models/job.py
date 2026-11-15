from datetime import datetime
from typing import Any, Dict, List
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, JSON, func
from app.core.database import Base


class JobDescription(Base):
    """
    Job Description database model storing both raw text and parsed criteria
    used by the matching engine.
    """
    __tablename__ = "job_descriptions"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    raw_text = Column(Text, nullable=False)

    # Parsed criteria stored as structured JSON
    required_skills = Column(JSON, default=list, nullable=False)
    core_skills = Column(JSON, default=list, nullable=True)
    preferred_skills = Column(JSON, default=list, nullable=False)
    min_experience = Column(Float, default=0.0, nullable=False)
    education = Column(JSON, default=list, nullable=False)
    keywords = Column(JSON, default=list, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def to_dict(self) -> Dict[str, Any]:
        """Convert database model to dictionary representation."""
        return {
            "id": self.id,
            "title": self.title,
            "raw_text": self.raw_text,
            "required_skills": self.required_skills or [],
            "core_skills": self.core_skills or [],
            "preferred_skills": self.preferred_skills or [],
            "min_experience": self.min_experience or 0.0,
            "education": self.education or [],
            "keywords": self.keywords or [],
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
