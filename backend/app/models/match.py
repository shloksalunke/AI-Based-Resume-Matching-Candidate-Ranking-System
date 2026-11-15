from datetime import datetime
from typing import Any, Dict, List
from sqlalchemy import Column, Integer, Float, DateTime, JSON, ForeignKey, func
from sqlalchemy.orm import relationship, backref
from app.core.database import Base


class MatchResult(Base):
    """
    MatchResult model storing scores and skill breakdown comparing a Resume against a JobDescription.
    """
    __tablename__ = "match_results"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("job_descriptions.id", ondelete="CASCADE"), nullable=False, index=True)
    resume_id = Column(Integer, ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False, index=True)

    overall_score = Column(Float, nullable=False)
    score_breakdown = Column(JSON, default=dict, nullable=False)
    matched_skills = Column(JSON, default=list, nullable=False)
    partially_matched_skills = Column(JSON, default=list, nullable=False)
    missing_skills = Column(JSON, default=list, nullable=False)
    reasons = Column(JSON, default=list, nullable=False)
    ai_summary = Column(JSON, nullable=True, default=None)
    llm_score = Column(Float, nullable=True, default=None)
    llm_analysis = Column(JSON, nullable=True, default=None)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships for convenient joins with proper cascade deletion
    job = relationship(
        "JobDescription",
        backref=backref("matches", cascade="all, delete-orphan", passive_deletes=True),
    )
    resume = relationship(
        "Resume",
        backref=backref("matches", cascade="all, delete-orphan", passive_deletes=True),
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert database model to dictionary representation."""
        return {
            "id": self.id,
            "job_id": self.job_id,
            "resume_id": self.resume_id,
            "overall_score": self.overall_score,
            "score_breakdown": self.score_breakdown or {},
            "matched_skills": self.matched_skills or [],
            "partially_matched_skills": self.partially_matched_skills or [],
            "missing_skills": self.missing_skills or [],
            "reasons": self.reasons or [],
            "ai_summary": self.ai_summary,
            "llm_score": self.llm_score,
            "llm_analysis": self.llm_analysis,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
