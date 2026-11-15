from datetime import datetime
from typing import Any, Dict, List, Optional
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, JSON, func
from app.core.database import Base


class Resume(Base):
    """
    Resume database model storing raw file content and extracted metadata.
    """
    __tablename__ = "resumes"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    raw_text = Column(Text, nullable=False)

    # Parsed structured profile
    name = Column(String(255), nullable=True, index=True)
    email = Column(String(255), nullable=True, index=True)
    phone = Column(String(50), nullable=True)
    skills = Column(JSON, default=list, nullable=False)
    total_experience_years = Column(Float, default=0.0, nullable=False)
    companies_and_designations = Column(JSON, default=list, nullable=False)
    education = Column(JSON, default=list, nullable=False)
    certifications = Column(JSON, default=list, nullable=False)
    projects = Column(JSON, default=list, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def to_dict(self) -> Dict[str, Any]:
        """Convert database model to dictionary representation."""
        return {
            "id": self.id,
            "filename": self.filename,
            "raw_text": self.raw_text,
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "skills": self.skills or [],
            "total_experience_years": self.total_experience_years or 0.0,
            "companies_and_designations": self.companies_and_designations or [],
            "education": self.education or [],
            "certifications": self.certifications or [],
            "projects": self.projects or [],
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
