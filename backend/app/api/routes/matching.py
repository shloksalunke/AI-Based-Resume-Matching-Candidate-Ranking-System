from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.models.job import JobDescription
from app.models.resume import Resume
from app.models.match import MatchResult
from app.schemas.match import (
    JobMatchRankedItem,
    JobMatchDetailedResponse,
    CandidateDetailedInfo,
    JobDetailedInfo,
)
from app.schemas.llm import CandidateAiSummary, CandidateAiEvaluation
from app.services.matching_service import calculate_match
from app.services.llm_service import is_llm_enabled, generate_candidate_summary, evaluate_candidate

router = APIRouter(prefix="/jobs", tags=["Matching"])


def _eval_candidate_worker(payload: tuple):
    match_id, jd_req, c_prof, s_res = payload
    result = evaluate_candidate(jd_req, c_prof, s_res)
    return match_id, result


@router.post("/{job_id}/match", response_model=List[JobMatchRankedItem], status_code=status.HTTP_200_OK)
def run_job_matching(
    job_id: int,
    scoring_mode: str = Query("standard", pattern="^(standard|ai)$"),
    db: Session = Depends(get_db),
):
    """
    Executes the matching engine for all uploaded resumes against the specified job.
    Replaces any previous MatchResult entries for this job and returns the ranked candidate list.
    Supports scoring_mode="standard" (default, fully deterministic) or "ai" (LLM evaluation for top candidates).
    """
    job = db.query(JobDescription).filter(JobDescription.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job description with ID {job_id} not found",
        )

    if scoring_mode == "ai" and not is_llm_enabled():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI scoring mode is unavailable because LLM is disabled or GEMINI_API_KEY is missing.",
        )

    resumes = db.query(Resume).all()
    if not resumes:
        return []

    # Clear existing match results for this job
    db.query(MatchResult).filter(MatchResult.job_id == job_id).delete()
    db.commit()

    created_matches: List[MatchResult] = []

    for resume in resumes:
        match_output = calculate_match(
            jd_title=job.title,
            jd_raw_text=job.raw_text,
            jd_required_skills=job.required_skills or [],
            jd_preferred_skills=job.preferred_skills or [],
            jd_min_experience=job.min_experience or 0.0,
            jd_education=job.education or [],
            resume_raw_text=resume.raw_text,
            resume_skills=resume.skills or [],
            resume_experience_years=resume.total_experience_years or 0.0,
            resume_education=resume.education or [],
            resume_certifications=resume.certifications or [],
            resume_projects=resume.projects or [],
            jd_core_skills=getattr(job, "core_skills", None) or [],
        )

        match_row = MatchResult(
            job_id=job.id,
            resume_id=resume.id,
            overall_score=match_output["overall_score"],
            score_breakdown=match_output["score_breakdown"],
            matched_skills=match_output["matched_skills"],
            partially_matched_skills=match_output["partially_matched_skills"],
            missing_skills=match_output["missing_skills"],
            reasons=match_output["reasons"],
        )
        db.add(match_row)
        created_matches.append(match_row)

    db.commit()

    # Re-query sorted by overall score descending
    sorted_matches = (
        db.query(MatchResult, Resume)
        .join(Resume, MatchResult.resume_id == Resume.id)
        .filter(MatchResult.job_id == job_id)
        .order_by(MatchResult.overall_score.desc())
        .all()
    )

    # Optional AI scoring mode for top candidates
    if scoring_mode == "ai" and sorted_matches:
        top_candidates = sorted_matches[: settings.LLM_MAX_CANDIDATES]

        jd_requirements = {
            "title": job.title,
            "min_experience": job.min_experience or 0.0,
            "required_skills": job.required_skills or [],
            "preferred_skills": job.preferred_skills or [],
            "core_skills": getattr(job, "core_skills", None) or [],
            "education": job.education or [],
        }

        eval_tasks = []
        for match, resume in top_candidates:
            c_profile = {
                "name": resume.name,
                "filename": resume.filename,
                "total_experience_years": resume.total_experience_years or 0.0,
                "skills": resume.skills or [],
                "education": resume.education or [],
            }
            s_result = {
                "overall_score": match.overall_score,
                "score_breakdown": match.score_breakdown or {},
                "matched_skills": match.matched_skills or [],
                "partially_matched_skills": match.partially_matched_skills or [],
                "missing_skills": match.missing_skills or [],
                "reasons": match.reasons or [],
            }
            eval_tasks.append((match.id, jd_requirements, c_profile, s_result))

        eval_results_map = {}
        with ThreadPoolExecutor(max_workers=settings.LLM_MAX_CONCURRENCY) as executor:
            future_to_id = {
                executor.submit(_eval_candidate_worker, task): task[0]
                for task in eval_tasks
            }
            for future in as_completed(future_to_id):
                match_id = future_to_id[future]
                try:
                    _, res = future.result()
                    eval_results_map[match_id] = res
                except Exception as exc:
                    eval_results_map[match_id] = {"error": f"Evaluation error: {str(exc)}"}

        for match, _ in sorted_matches:
            if match.id in eval_results_map:
                res = eval_results_map[match.id]
                if res.get("error"):
                    match.llm_score = None
                    match.llm_analysis = res
                else:
                    match.llm_score = res.get("ai_score")
                    match.llm_analysis = res
                    match.ai_summary = {
                        "summary": res.get("summary", ""),
                        "strengths": res.get("strengths", []),
                        "concerns": res.get("concerns", []),
                        "recommendation": res.get("recommendation", "Possible fit"),
                    }

        db.commit()

    ranked_results: List[JobMatchRankedItem] = []
    for rank, (match, resume) in enumerate(sorted_matches, start=1):
        ranked_results.append(
            JobMatchRankedItem(
                match_id=match.id,
                resume_id=resume.id,
                filename=resume.filename,
                name=resume.name,
                email=resume.email,
                total_experience_years=resume.total_experience_years or 0.0,
                overall_score=match.overall_score,
                score_breakdown=match.score_breakdown or {},
                matched_skills=match.matched_skills or [],
                partially_matched_skills=match.partially_matched_skills or [],
                missing_skills=match.missing_skills or [],
                llm_score=match.llm_score,
                llm_analysis=match.llm_analysis,
                rank=rank,
            )
        )

    return ranked_results


@router.get("/{job_id}/results", response_model=List[JobMatchRankedItem])
@router.get("/{job_id}/matches", response_model=List[JobMatchRankedItem])
def get_job_results(job_id: int, db: Session = Depends(get_db)):
    """
    Returns ranked match results for a job description.
    """
    job = db.query(JobDescription).filter(JobDescription.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job description with ID {job_id} not found",
        )

    matches_with_resumes = (
        db.query(MatchResult, Resume)
        .join(Resume, MatchResult.resume_id == Resume.id)
        .filter(MatchResult.job_id == job_id)
        .order_by(MatchResult.overall_score.desc())
        .all()
    )

    ranked_results: List[JobMatchRankedItem] = []
    for rank, (match, resume) in enumerate(matches_with_resumes, start=1):
        ranked_results.append(
            JobMatchRankedItem(
                match_id=match.id,
                resume_id=resume.id,
                filename=resume.filename,
                name=resume.name,
                email=resume.email,
                total_experience_years=resume.total_experience_years or 0.0,
                overall_score=match.overall_score,
                score_breakdown=match.score_breakdown or {},
                matched_skills=match.matched_skills or [],
                partially_matched_skills=match.partially_matched_skills or [],
                missing_skills=match.missing_skills or [],
                llm_score=match.llm_score,
                llm_analysis=match.llm_analysis,
                rank=rank,
            )
        )

    return ranked_results


@router.get("/{job_id}/results/{resume_id}", response_model=JobMatchDetailedResponse)
def get_job_match_detail(job_id: int, resume_id: int, db: Session = Depends(get_db)):
    """
    Returns full in-depth comparison analysis between a specific resume and job description.
    """
    job = db.query(JobDescription).filter(JobDescription.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job description with ID {job_id} not found",
        )

    resume = db.query(Resume).filter(Resume.id == resume_id).first()
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Resume with ID {resume_id} not found",
        )

    match = (
        db.query(MatchResult)
        .filter(MatchResult.job_id == job_id, MatchResult.resume_id == resume_id)
        .first()
    )

    # If matching has not been run yet for this pair, calculate it dynamically
    if not match:
        match_output = calculate_match(
            jd_title=job.title,
            jd_raw_text=job.raw_text,
            jd_required_skills=job.required_skills or [],
            jd_preferred_skills=job.preferred_skills or [],
            jd_min_experience=job.min_experience or 0.0,
            jd_education=job.education or [],
            resume_raw_text=resume.raw_text,
            resume_skills=resume.skills or [],
            resume_experience_years=resume.total_experience_years or 0.0,
            resume_education=resume.education or [],
            resume_certifications=resume.certifications or [],
            resume_projects=resume.projects or [],
            jd_core_skills=getattr(job, "core_skills", None) or [],
        )
        match = MatchResult(
            job_id=job.id,
            resume_id=resume.id,
            overall_score=match_output["overall_score"],
            score_breakdown=match_output["score_breakdown"],
            matched_skills=match_output["matched_skills"],
            partially_matched_skills=match_output["partially_matched_skills"],
            missing_skills=match_output["missing_skills"],
            reasons=match_output["reasons"],
        )
        db.add(match)
        db.commit()
        db.refresh(match)

    candidate_info = CandidateDetailedInfo(
        resume_id=resume.id,
        filename=resume.filename,
        name=resume.name,
        email=resume.email,
        phone=resume.phone,
        skills=resume.skills or [],
        total_experience_years=resume.total_experience_years or 0.0,
        companies_and_designations=resume.companies_and_designations or [],
        education=resume.education or [],
        certifications=resume.certifications or [],
        projects=resume.projects or [],
    )

    job_info = JobDetailedInfo(
        job_id=job.id,
        title=job.title,
        min_experience=job.min_experience or 0.0,
        required_skills=job.required_skills or [],
        core_skills=getattr(job, "core_skills", None) or [],
        preferred_skills=job.preferred_skills or [],
        education=job.education or [],
    )

    return JobMatchDetailedResponse(
        match_id=match.id,
        overall_score=match.overall_score,
        score_breakdown=match.score_breakdown or {},
        matched_skills=match.matched_skills or [],
        partially_matched_skills=match.partially_matched_skills or [],
        missing_skills=match.missing_skills or [],
        reasons=match.reasons or [],
        ai_summary=match.ai_summary,
        llm_score=match.llm_score,
        llm_analysis=match.llm_analysis,
        created_at=match.created_at,
        candidate=candidate_info,
        job=job_info,
    )


@router.post("/{job_id}/results/{resume_id}/ai-review", response_model=CandidateAiEvaluation)
def get_or_run_candidate_ai_review(
    job_id: int,
    resume_id: int,
    refresh: bool = Query(False),
    db: Session = Depends(get_db),
):
    """
    Executes or retrieves the detailed AI candidate evaluation for a specific candidate.
    Cached unless ?refresh=true.
    Returns 503 if LLM is disabled or GEMINI_API_KEY is missing.
    """
    job = db.query(JobDescription).filter(JobDescription.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job description with ID {job_id} not found",
        )

    resume = db.query(Resume).filter(Resume.id == resume_id).first()
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Resume with ID {resume_id} not found",
        )

    match = (
        db.query(MatchResult)
        .filter(MatchResult.job_id == job_id, MatchResult.resume_id == resume_id)
        .first()
    )

    if not match:
        match_output = calculate_match(
            jd_title=job.title,
            jd_raw_text=job.raw_text,
            jd_required_skills=job.required_skills or [],
            jd_preferred_skills=job.preferred_skills or [],
            jd_min_experience=job.min_experience or 0.0,
            jd_education=job.education or [],
            resume_raw_text=resume.raw_text,
            resume_skills=resume.skills or [],
            resume_experience_years=resume.total_experience_years or 0.0,
            resume_education=resume.education or [],
            resume_certifications=resume.certifications or [],
            resume_projects=resume.projects or [],
            jd_core_skills=getattr(job, "core_skills", None) or [],
        )
        match = MatchResult(
            job_id=job.id,
            resume_id=resume.id,
            overall_score=match_output["overall_score"],
            score_breakdown=match_output["score_breakdown"],
            matched_skills=match_output["matched_skills"],
            partially_matched_skills=match_output["partially_matched_skills"],
            missing_skills=match_output["missing_skills"],
            reasons=match_output["reasons"],
        )
        db.add(match)
        db.commit()
        db.refresh(match)

    # 1. Return cached evaluation if available and refresh is False (and no previous error)
    if not refresh and match.llm_analysis and not match.llm_analysis.get("error"):
        return CandidateAiEvaluation(**match.llm_analysis)

    # 2. Check if LLM is enabled
    if not is_llm_enabled():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI scoring mode is unavailable because LLM is disabled or GEMINI_API_KEY is missing.",
        )

    # 3. Build compact context and evaluate
    candidate_profile = {
        "name": resume.name,
        "filename": resume.filename,
        "total_experience_years": resume.total_experience_years or 0.0,
        "skills": resume.skills or [],
        "education": resume.education or [],
    }
    jd_requirements = {
        "title": job.title,
        "min_experience": job.min_experience or 0.0,
        "required_skills": job.required_skills or [],
        "preferred_skills": job.preferred_skills or [],
        "core_skills": getattr(job, "core_skills", None) or [],
        "education": job.education or [],
    }
    standard_result = {
        "overall_score": match.overall_score,
        "score_breakdown": match.score_breakdown or {},
        "matched_skills": match.matched_skills or [],
        "partially_matched_skills": match.partially_matched_skills or [],
        "missing_skills": match.missing_skills or [],
        "reasons": match.reasons or [],
    }

    eval_data = evaluate_candidate(jd_requirements, candidate_profile, standard_result)

    if eval_data.get("error"):
        match.llm_score = None
        match.llm_analysis = eval_data
    else:
        match.llm_score = eval_data.get("ai_score")
        match.llm_analysis = eval_data
        match.ai_summary = {
            "summary": eval_data.get("summary", ""),
            "strengths": eval_data.get("strengths", []),
            "concerns": eval_data.get("concerns", []),
            "recommendation": eval_data.get("recommendation", "Possible fit"),
        }

    db.commit()
    db.refresh(match)

    return CandidateAiEvaluation(**eval_data)


@router.post("/{job_id}/results/{resume_id}/ai-summary", response_model=CandidateAiSummary)
def get_or_generate_ai_summary(
    job_id: int,
    resume_id: int,
    db: Session = Depends(get_db),
):
    """
    Returns cached AI executive summary if available; otherwise generates, caches, and returns it.
    Returns 503 if LLM layer is disabled or GEMINI_API_KEY is not configured.
    """
    job = db.query(JobDescription).filter(JobDescription.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job description with ID {job_id} not found",
        )

    resume = db.query(Resume).filter(Resume.id == resume_id).first()
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Resume with ID {resume_id} not found",
        )

    match = (
        db.query(MatchResult)
        .filter(MatchResult.job_id == job_id, MatchResult.resume_id == resume_id)
        .first()
    )

    if not match:
        match_output = calculate_match(
            jd_title=job.title,
            jd_raw_text=job.raw_text,
            jd_required_skills=job.required_skills or [],
            jd_preferred_skills=job.preferred_skills or [],
            jd_min_experience=job.min_experience or 0.0,
            jd_education=job.education or [],
            resume_raw_text=resume.raw_text,
            resume_skills=resume.skills or [],
            resume_experience_years=resume.total_experience_years or 0.0,
            resume_education=resume.education or [],
            resume_certifications=resume.certifications or [],
            resume_projects=resume.projects or [],
            jd_core_skills=getattr(job, "core_skills", None) or [],
        )
        match = MatchResult(
            job_id=job.id,
            resume_id=resume.id,
            overall_score=match_output["overall_score"],
            score_breakdown=match_output["score_breakdown"],
            matched_skills=match_output["matched_skills"],
            partially_matched_skills=match_output["partially_matched_skills"],
            missing_skills=match_output["missing_skills"],
            reasons=match_output["reasons"],
        )
        db.add(match)
        db.commit()
        db.refresh(match)

    # 1. Return cached summary if present
    if match.ai_summary:
        return CandidateAiSummary(**match.ai_summary)

    # 2. Check if LLM is enabled
    if not is_llm_enabled():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="LLM service is disabled or GEMINI_API_KEY is missing. Enable USE_LLM=true in .env to use this feature.",
        )

    # 3. Generate summary using compact prompt
    candidate_profile = {
        "name": resume.name,
        "filename": resume.filename,
        "total_experience_years": resume.total_experience_years or 0.0,
        "skills": resume.skills or [],
        "education": resume.education or [],
    }
    jd_requirements = {
        "title": job.title,
        "min_experience": job.min_experience or 0.0,
        "required_skills": job.required_skills or [],
        "core_skills": getattr(job, "core_skills", None) or [],
    }
    score_result = {
        "overall_score": match.overall_score,
        "score_breakdown": match.score_breakdown or {},
        "matched_skills": match.matched_skills or [],
        "partially_matched_skills": match.partially_matched_skills or [],
        "missing_skills": match.missing_skills or [],
        "reasons": match.reasons or [],
    }

    summary_data = generate_candidate_summary(candidate_profile, jd_requirements, score_result)
    if not summary_data:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to generate AI summary from LLM service.",
        )

    # 4. Cache and commit
    match.ai_summary = summary_data
    db.commit()
    db.refresh(match)

    return CandidateAiSummary(**summary_data)

