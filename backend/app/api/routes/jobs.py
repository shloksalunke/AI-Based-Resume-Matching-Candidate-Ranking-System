import os
import shutil
import tempfile
from typing import List, Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status, Request
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.core.config import settings
from app.core.database import get_db
from app.models.job import JobDescription
from app.models.match import MatchResult
from app.schemas.job import JobDescriptionResponse
from app.services.jd_service import parse_job_description, parse_job_file

router = APIRouter(prefix="/jobs", tags=["Jobs"])

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".doc", ".txt"}
MAX_FILE_BYTES = settings.MAX_FILE_SIZE_MB * 1024 * 1024


@router.post("", response_model=JobDescriptionResponse, status_code=status.HTTP_201_CREATED)
async def create_job(
    request: Request,
    title: Optional[str] = Form(None),
    raw_text: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
):
    """
    Creates a new Job Description either from pasted plain text or an uploaded document (PDF/DOCX/TXT).
    Supports both multipart/form-data and JSON request payloads.
    """
    final_title = title
    final_raw_text = raw_text

    # If the request is JSON instead of multipart/form-data
    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        body = await request.json()
        final_title = body.get("title")
        final_raw_text = body.get("raw_text")

    # If a file was uploaded, extract text from it
    if file and file.filename:
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file format '{ext}'. Allowed: {', '.join(ALLOWED_EXTENSIONS)}",
            )

        # Check file size
        file_bytes = await file.read()
        if len(file_bytes) > MAX_FILE_BYTES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File exceeds maximum allowed size of {settings.MAX_FILE_SIZE_MB}MB",
            )

        # Write to temp file to reuse parser_service
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
            tmp.write(file_bytes)
            tmp_path = tmp.name

        try:
            extracted_text, parsed_data = parse_job_file(tmp_path)
            final_raw_text = extracted_text
            if not final_title:
                # Infer title from filename without extension
                final_title = os.path.splitext(file.filename)[0].replace("_", " ").title()
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    # Validate that we have text content
    if not final_raw_text or not final_raw_text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Job description text is required (either provide raw_text or upload a file).",
        )

    if not final_title or not final_title.strip():
        # Fallback title if none provided
        first_line = final_raw_text.strip().split("\n")[0][:60]
        final_title = first_line if first_line else "Untitled Job Description"

    # Parse criteria from the raw text
    parsed = parse_job_description(final_raw_text, title=final_title.strip())

    # Persist in DB
    job = JobDescription(
        title=final_title.strip(),
        raw_text=final_raw_text.strip(),
        required_skills=parsed["required_skills"],
        core_skills=parsed.get("core_skills", []),
        preferred_skills=parsed["preferred_skills"],
        min_experience=parsed["min_experience"],
        education=parsed["education"],
        keywords=parsed["keywords"],
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    return job


@router.get("", response_model=List[JobDescriptionResponse])
def list_jobs(db: Session = Depends(get_db)):
    """Retrieves all registered job descriptions ordered by newest first."""
    jobs = db.query(JobDescription).order_by(JobDescription.created_at.desc()).all()
    return jobs


@router.get("/{job_id}", response_model=JobDescriptionResponse)
def get_job(job_id: int, db: Session = Depends(get_db)):
    """Retrieves a single job description by ID."""
    job = db.query(JobDescription).filter(JobDescription.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job description with ID {job_id} not found",
        )
    return job


@router.delete("/{job_id}", status_code=status.HTTP_200_OK)
def delete_job(job_id: int, db: Session = Depends(get_db)):
    """Deletes a job description and its associated match results."""
    job = db.query(JobDescription).filter(JobDescription.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job description with ID {job_id} not found",
        )
    # Explicitly clear referencing match results before deleting the job
    db.query(MatchResult).filter(MatchResult.job_id == job_id).delete()
    db.delete(job)
    db.commit()
    return {"message": "Job description deleted successfully", "id": job_id}
