import os
import tempfile
from typing import List
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.models.resume import Resume
from app.models.match import MatchResult
from app.schemas.resume import (
    ResumeResponse,
    ResumeUploadResult,
    ResumeUploadBatchResponse,
)
from app.services.parser_service import parse_resume_file

router = APIRouter(prefix="/resumes", tags=["Resumes"])

ALLOWED_RESUME_EXTENSIONS = {".pdf", ".docx", ".doc"}
MAX_FILE_BYTES = settings.MAX_FILE_SIZE_MB * 1024 * 1024


@router.post("/upload", response_model=ResumeUploadBatchResponse, status_code=status.HTTP_200_OK)
async def upload_resumes(
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
):
    """
    Uploads multiple resumes (PDF/DOCX) in batches.
    Validates per-file extension and size; returns individual success/failure reports
    so that single erroneous files do not block the entire batch.
    """
    results: List[ResumeUploadResult] = []
    success_count = 0
    failure_count = 0

    # Ensure upload directory exists if needed for permanent storage
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

    for upload in files:
        filename = upload.filename or "unknown_resume"
        ext = os.path.splitext(filename)[1].lower()

        if ext not in ALLOWED_RESUME_EXTENSIONS:
            results.append(
                ResumeUploadResult(
                    filename=filename,
                    status="error",
                    error_message=f"Unsupported file format '{ext}'. Only PDF and DOCX files are accepted.",
                )
            )
            failure_count += 1
            continue

        try:
            content = await upload.read()
            if len(content) > MAX_FILE_BYTES:
                results.append(
                    ResumeUploadResult(
                        filename=filename,
                        status="error",
                        error_message=f"File exceeds maximum allowed limit of {settings.MAX_FILE_SIZE_MB}MB.",
                    )
                )
                failure_count += 1
                continue

            # Write temporary file for parsing
            with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
                tmp.write(content)
                tmp_path = tmp.name

            try:
                parsed_data = parse_resume_file(tmp_path)
            finally:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)

            # Persist resume record into database
            resume_record = Resume(
                filename=filename,
                raw_text=parsed_data.get("raw_text", ""),
                name=parsed_data.get("name"),
                email=parsed_data.get("email"),
                phone=parsed_data.get("phone"),
                skills=parsed_data.get("skills", []),
                total_experience_years=parsed_data.get("total_experience_years", 0.0),
                companies_and_designations=parsed_data.get("companies_and_designations", []),
                education=parsed_data.get("education", []),
                certifications=parsed_data.get("certifications", []),
                projects=parsed_data.get("projects", []),
            )
            db.add(resume_record)
            db.commit()
            db.refresh(resume_record)

            results.append(
                ResumeUploadResult(
                    filename=filename,
                    status="success",
                    resume_id=resume_record.id,
                    candidate_name=resume_record.name,
                )
            )
            success_count += 1

        except Exception as e:
            db.rollback()
            results.append(
                ResumeUploadResult(
                    filename=filename,
                    status="error",
                    error_message=f"Failed to process resume: {str(e)}",
                )
            )
            failure_count += 1

    return ResumeUploadBatchResponse(
        total=len(files),
        successful=success_count,
        failed=failure_count,
        results=results,
    )


@router.get("", response_model=List[ResumeResponse])
def list_resumes(db: Session = Depends(get_db)):
    """Retrieves all parsed resumes ordered by upload date descending."""
    resumes = db.query(Resume).order_by(Resume.created_at.desc()).all()
    return resumes


@router.get("/{resume_id}", response_model=ResumeResponse)
def get_resume(resume_id: int, db: Session = Depends(get_db)):
    """Retrieves a single parsed resume profile by ID."""
    resume = db.query(Resume).filter(Resume.id == resume_id).first()
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Resume with ID {resume_id} not found",
        )
    return resume


@router.delete("/{resume_id}", status_code=status.HTTP_200_OK)
def delete_resume(resume_id: int, db: Session = Depends(get_db)):
    """Deletes a resume and cascade deletes any associated match results."""
    resume = db.query(Resume).filter(Resume.id == resume_id).first()
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Resume with ID {resume_id} not found",
        )
    # Explicitly clear referencing match results before deleting the resume
    db.query(MatchResult).filter(MatchResult.resume_id == resume_id).delete()
    db.delete(resume)
    db.commit()
    return {"message": "Resume deleted successfully", "id": resume_id}
