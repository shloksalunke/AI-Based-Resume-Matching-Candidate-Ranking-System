import json
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from app.main import app
from app.core.config import settings
from app.models.job import JobDescription
from app.models.resume import Resume
from app.models.match import MatchResult
from app.core.database import SessionLocal

client = TestClient(app)


@pytest.fixture
def sample_job_and_resume():
    """Seeds a test job and resume for testing AI summary."""
    db = SessionLocal()
    db.query(MatchResult).delete()
    db.query(Resume).delete()
    db.query(JobDescription).delete()
    db.commit()

    job = JobDescription(
        title="Senior Python Backend Developer",
        raw_text="Job Title: Senior Python Backend Developer\nRequirements: Python, FastAPI, Docker, PostgreSQL\nExperience: 4+ years",
        required_skills=["Python", "FastAPI", "Docker", "PostgreSQL"],
        core_skills=["Python", "FastAPI"],
        preferred_skills=["AWS", "Redis"],
        min_experience=4.0,
        education=["B.Tech"],
        keywords=["python", "fastapi", "backend"],
    )
    db.add(job)

    resume = Resume(
        filename="test_candidate.pdf",
        raw_text="Jane Doe\nPython Developer with 5 years experience in Python, FastAPI, Docker, PostgreSQL.",
        name="Jane Doe",
        email="jane.doe@test.com",
        phone="555-0199",
        skills=["Python", "FastAPI", "Docker", "PostgreSQL"],
        total_experience_years=5.0,
        companies_and_designations=[{"company": "Tech Corp", "designation": "Backend Engineer"}],
        education=[{"degree": "B.Tech"}],
        certifications=[],
        projects=[{"title": "API Engine"}],
    )
    db.add(resume)
    db.commit()
    db.refresh(job)
    db.refresh(resume)

    job_id = job.id
    resume_id = resume.id
    db.close()

    return job_id, resume_id


def test_llm_status_endpoint():
    """GET /api/llm/status reflects current configuration and max_candidates."""
    with patch.object(settings, "USE_LLM", False):
        resp = client.get("/api/llm/status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["enabled"] is False
        assert data["max_candidates"] == settings.LLM_MAX_CANDIDATES

    with patch.object(settings, "USE_LLM", True), patch.object(settings, "GEMINI_API_KEY", "dummy_key"):
        resp = client.get("/api/llm/status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["enabled"] is True
        assert data["max_candidates"] == settings.LLM_MAX_CANDIDATES


def test_ai_summary_disabled_returns_503(sample_job_and_resume):
    """POST ai-summary returns 503 when USE_LLM=False or key missing."""
    job_id, resume_id = sample_job_and_resume

    with patch.object(settings, "USE_LLM", False):
        resp = client.post(f"/api/jobs/{job_id}/results/{resume_id}/ai-summary")
        assert resp.status_code == 503
        assert "disabled" in resp.json()["detail"].lower()


def test_ai_summary_valid_json_parsed_and_cached(sample_job_and_resume):
    """
    Valid LLM response is parsed into CandidateAiSummary schema and cached in DB.
    Subsequent call returns cached result without invoking LLM again.
    """
    job_id, resume_id = sample_job_and_resume
    mock_llm_output = {
        "summary": "Jane Doe is a strong candidate with 5 years of solid Python and FastAPI development experience.",
        "strengths": [
            "Demonstrated 5 years hands-on experience meeting the 4-year requirement",
            "Matched 100% of core skills including Python and FastAPI",
            "Strong background in containerized Docker microservices",
        ],
        "concerns": ["No explicit cloud AWS experience mentioned"],
        "recommendation": "Strong fit",
    }

    mock_response = MagicMock()
    mock_response.text = f"```json\n{json.dumps(mock_llm_output)}\n```"

    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = mock_response

    with patch.object(settings, "USE_LLM", True), \
         patch.object(settings, "GEMINI_API_KEY", "fake_key_123"), \
         patch("google.genai.Client", return_value=mock_client):

        # 1. First call: Generates and returns summary
        resp = client.post(f"/api/jobs/{job_id}/results/{resume_id}/ai-summary")
        assert resp.status_code == 200, f"Error: {resp.text}"
        data = resp.json()
        assert data["recommendation"] == "Strong fit"
        assert len(data["strengths"]) == 3
        assert len(data["concerns"]) == 1
        assert mock_client.models.generate_content.call_count == 1

        # 2. Verify summary is stored in database
        db = SessionLocal()
        match = db.query(MatchResult).filter(MatchResult.job_id == job_id, MatchResult.resume_id == resume_id).first()
        assert match is not None
        assert match.ai_summary is not None
        assert match.ai_summary["recommendation"] == "Strong fit"
        db.close()

        # 3. Second call: Should return cached summary without calling generate_content again
        resp_cached = client.post(f"/api/jobs/{job_id}/results/{resume_id}/ai-summary")
        assert resp_cached.status_code == 200
        assert resp_cached.json()["recommendation"] == "Strong fit"
        # call_count should still be 1 (cached!)
        assert mock_client.models.generate_content.call_count == 1


def test_ai_summary_malformed_llm_output_returns_502(sample_job_and_resume):
    """Malformed non-JSON output from LLM is handled cleanly and returns 502."""
    job_id, resume_id = sample_job_and_resume

    # Ensure match exists and has no ai_summary
    db = SessionLocal()
    match = db.query(MatchResult).filter(MatchResult.job_id == job_id, MatchResult.resume_id == resume_id).first()
    if match:
        match.ai_summary = None
        db.commit()
    db.close()

    mock_response = MagicMock()
    mock_response.text = "I cannot fulfill this request properly. Error 500."

    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = mock_response

    with patch.object(settings, "USE_LLM", True), \
         patch.object(settings, "GEMINI_API_KEY", "fake_key_123"), \
         patch("google.genai.Client", return_value=mock_client):

        resp = client.post(f"/api/jobs/{job_id}/results/{resume_id}/ai-summary")
        assert resp.status_code == 502
        assert "failed" in resp.json()["detail"].lower()


def test_scores_remain_strictly_unchanged_after_generating_summary(sample_job_and_resume):
    """
    Guarantees that the AI summary layer does NOT alter any scores, weights, or breakdown components.
    """
    job_id, resume_id = sample_job_and_resume

    # Get match details before summary
    detail_before = client.get(f"/api/jobs/{job_id}/results/{resume_id}").json()
    score_before = detail_before["overall_score"]
    breakdown_before = detail_before["score_breakdown"]
    matched_before = detail_before["matched_skills"]

    mock_llm_output = {
        "summary": "Solid backend profile matching requirements.",
        "strengths": ["Strong Python foundation"],
        "concerns": [],
        "recommendation": "Strong fit",
    }
    mock_response = MagicMock()
    mock_response.text = json.dumps(mock_llm_output)

    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = mock_response

    with patch.object(settings, "USE_LLM", True), \
         patch.object(settings, "GEMINI_API_KEY", "fake_key_123"), \
         patch("google.genai.Client", return_value=mock_client):

        # Generate summary
        summary_resp = client.post(f"/api/jobs/{job_id}/results/{resume_id}/ai-summary")
        assert summary_resp.status_code == 200

    # Get match details after summary
    detail_after = client.get(f"/api/jobs/{job_id}/results/{resume_id}").json()

    # Scores must be 100% identical
    assert detail_after["overall_score"] == score_before
    assert detail_after["score_breakdown"] == breakdown_before
    assert detail_after["matched_skills"] == matched_before
    # AI summary is now populated
    assert detail_after["ai_summary"] is not None
    assert detail_after["ai_summary"]["recommendation"] == "Strong fit"


def test_ai_scoring_mode_disabled_returns_503(sample_job_and_resume):
    """POST /api/jobs/{job_id}/match?scoring_mode=ai returns 503 when LLM is disabled."""
    job_id, _ = sample_job_and_resume
    with patch.object(settings, "USE_LLM", False):
        resp = client.post(f"/api/jobs/{job_id}/match?scoring_mode=ai")
        assert resp.status_code == 503
        assert "unavailable" in resp.json()["detail"].lower()


def test_ai_review_disabled_returns_503(sample_job_and_resume):
    """POST /api/jobs/{job_id}/results/{resume_id}/ai-review returns 503 when LLM is disabled."""
    job_id, resume_id = sample_job_and_resume
    with patch.object(settings, "USE_LLM", False):
        resp = client.post(f"/api/jobs/{job_id}/results/{resume_id}/ai-review?refresh=true")
        assert resp.status_code == 503
        assert "unavailable" in resp.json()["detail"].lower()


def test_ai_scoring_score_clamping():
    """CandidateAiEvaluation clamps scores outside 0-100 and limits lists."""
    from app.schemas.llm import CandidateAiEvaluation

    # Score > 100 clamped to 100.0
    ev_high = CandidateAiEvaluation(ai_score=135.5, strengths=["s1", "s2", "s3", "s4", "s5"])
    assert ev_high.ai_score == 100.0
    assert len(ev_high.strengths) == 3

    # Score < 0 clamped to 0.0
    ev_low = CandidateAiEvaluation(ai_score=-20.0, concerns=["c1", "c2", "c3", "c4"])
    assert ev_low.ai_score == 0.0
    assert len(ev_low.concerns) == 3


def test_ai_scoring_mode_valid_flow(sample_job_and_resume):
    """
    POST /api/jobs/{job_id}/match?scoring_mode=ai executes standard match + AI candidate evaluation,
    storing llm_score and llm_analysis.
    """
    job_id, resume_id = sample_job_and_resume

    mock_llm_output = {
        "ai_score": 92.5,
        "matched_skills": ["Python", "FastAPI", "Docker"],
        "missing_skills": [],
        "equivalent_skills": ["PostgreSQL ~ Relational SQL"],
        "experience_assessment": "Exceeds 4-year requirement with 5 years experience.",
        "summary": "Outstanding candidate for backend development.",
        "strengths": ["Deep Python expertise", "Production FastAPI usage", "Docker deployment"],
        "concerns": [],
        "recommendation": "Strong fit",
        "reasons": ["Core skills matched", "Experience verified"],
    }

    mock_response = MagicMock()
    mock_response.text = f"```json\n{json.dumps(mock_llm_output)}\n```"

    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = mock_response

    with patch.object(settings, "USE_LLM", True), \
         patch.object(settings, "GEMINI_API_KEY", "fake_key_123"), \
         patch("google.genai.Client", return_value=mock_client):

        resp = client.post(f"/api/jobs/{job_id}/match?scoring_mode=ai")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 1
        top_cand = next(c for c in data if c["resume_id"] == resume_id)
        assert top_cand["llm_score"] == 92.5
        assert top_cand["llm_analysis"] is not None
        assert top_cand["llm_analysis"]["recommendation"] == "Strong fit"
        assert top_cand["llm_analysis"]["ai_score"] == 92.5

        # Verify DB persistence
        db = SessionLocal()
        match = db.query(MatchResult).filter(MatchResult.job_id == job_id, MatchResult.resume_id == resume_id).first()
        assert match is not None
        assert match.llm_score == 92.5
        assert match.llm_analysis["recommendation"] == "Strong fit"
        db.close()


def test_ai_scoring_mode_batch_resilience_one_failure():
    """
    In a batch with multiple candidates, if one candidate fails evaluation,
    it records error in llm_analysis and does not break the batch or other candidates.
    """
    db = SessionLocal()
    db.query(MatchResult).delete()
    db.query(Resume).delete()
    db.query(JobDescription).delete()
    db.commit()

    job = JobDescription(
        title="Fullstack Python Engineer",
        raw_text="Python React Developer",
        required_skills=["Python", "React"],
        core_skills=["Python"],
    )
    db.add(job)

    r1 = Resume(
        filename="good_cand.pdf",
        raw_text="Good candidate with Python and React expertise",
        name="Good Cand",
        skills=["Python", "React"],
        total_experience_years=3.0,
    )
    r2 = Resume(
        filename="err_cand.pdf",
        raw_text="Err candidate with Python",
        name="Err Cand",
        skills=["Python"],
        total_experience_years=2.0,
    )
    db.add(r1)
    db.add(r2)
    db.commit()
    db.refresh(job)
    db.refresh(r1)
    db.refresh(r2)
    job_id = job.id
    r1_id = r1.id
    r2_id = r2.id
    db.close()

    call_count = 0

    def mock_generate_content(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        contents = str(kwargs.get("contents", ""))
        mock_resp = MagicMock()
        if "good_cand.pdf" in contents or "Good Cand" in contents:
            mock_resp.text = json.dumps({
                "ai_score": 88.0,
                "matched_skills": ["Python", "React"],
                "missing_skills": [],
                "equivalent_skills": [],
                "experience_assessment": "Good fit",
                "summary": "Good profile",
                "strengths": ["Fullstack"],
                "concerns": [],
                "recommendation": "Strong fit",
                "reasons": ["All matched"],
            })
            return mock_resp
        else:
            # Simulate failure / malformed response for r2
            mock_resp.text = "NOT JSON ERROR"
            return mock_resp

    mock_client = MagicMock()
    mock_client.models.generate_content.side_effect = mock_generate_content

    with patch.object(settings, "USE_LLM", True), \
         patch.object(settings, "GEMINI_API_KEY", "fake_key_123"), \
         patch("google.genai.Client", return_value=mock_client):

        resp = client.post(f"/api/jobs/{job_id}/match?scoring_mode=ai")
        assert resp.status_code == 200
        items = resp.json()

        cand1 = next(c for c in items if c["resume_id"] == r1_id)
        cand2 = next(c for c in items if c["resume_id"] == r2_id)

        assert cand1["llm_score"] == 88.0
        assert cand1["llm_analysis"]["recommendation"] == "Strong fit"

        # Cand 2 has None for llm_score and error object in llm_analysis
        assert cand2["llm_score"] is None
        assert cand2["llm_analysis"] is not None
        assert "error" in cand2["llm_analysis"]


def test_standard_score_strictly_identical_before_and_after_ai_mode(sample_job_and_resume):
    """
    Verifies standard overall_score, score_breakdown, and rank are 100% identical
    whether matching is run in standard mode or AI mode.
    """
    job_id, resume_id = sample_job_and_resume

    # Run in standard mode
    resp_std = client.post(f"/api/jobs/{job_id}/match?scoring_mode=standard")
    assert resp_std.status_code == 200
    std_cand = next(c for c in resp_std.json() if c["resume_id"] == resume_id)
    std_overall = std_cand["overall_score"]
    std_breakdown = std_cand["score_breakdown"]
    std_rank = std_cand["rank"]

    # Run in AI mode
    mock_llm_output = {
        "ai_score": 70.0,
        "matched_skills": ["Python"],
        "missing_skills": [],
        "equivalent_skills": [],
        "experience_assessment": "Adequate",
        "summary": "Test candidate",
        "strengths": ["Python"],
        "concerns": [],
        "recommendation": "Possible fit",
        "reasons": ["Basic fit"],
    }
    mock_response = MagicMock()
    mock_response.text = json.dumps(mock_llm_output)
    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = mock_response

    with patch.object(settings, "USE_LLM", True), \
         patch.object(settings, "GEMINI_API_KEY", "fake_key_123"), \
         patch("google.genai.Client", return_value=mock_client):

        resp_ai = client.post(f"/api/jobs/{job_id}/match?scoring_mode=ai")
        assert resp_ai.status_code == 200
        ai_cand = next(c for c in resp_ai.json() if c["resume_id"] == resume_id)

    # Standard metrics MUST be exactly identical
    assert ai_cand["overall_score"] == std_overall
    assert ai_cand["score_breakdown"] == std_breakdown
    assert ai_cand["rank"] == std_rank
    assert ai_cand["llm_score"] == 70.0


def test_candidate_ai_review_cache_and_refresh(sample_job_and_resume):
    """
    POST /api/jobs/{job_id}/results/{resume_id}/ai-review caches analysis and respects ?refresh=true.
    """
    job_id, resume_id = sample_job_and_resume

    mock_eval_1 = {
        "ai_score": 85.0,
        "matched_skills": ["Python", "FastAPI"],
        "missing_skills": [],
        "equivalent_skills": [],
        "experience_assessment": "First review",
        "summary": "First summary",
        "strengths": ["Strength 1"],
        "concerns": [],
        "recommendation": "Strong fit",
        "reasons": ["R1"],
    }

    mock_eval_2 = {
        "ai_score": 90.0,
        "matched_skills": ["Python", "FastAPI", "Docker"],
        "missing_skills": [],
        "equivalent_skills": [],
        "experience_assessment": "Refreshed review",
        "summary": "Refreshed summary",
        "strengths": ["Strength 1", "Strength 2"],
        "concerns": [],
        "recommendation": "Strong fit",
        "reasons": ["R1", "R2"],
    }

    mock_response = MagicMock()
    mock_response.text = json.dumps(mock_eval_1)
    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = mock_response

    with patch.object(settings, "USE_LLM", True), \
         patch.object(settings, "GEMINI_API_KEY", "fake_key_123"), \
         patch("google.genai.Client", return_value=mock_client):

        # First call generates
        resp1 = client.post(f"/api/jobs/{job_id}/results/{resume_id}/ai-review?refresh=true")
        assert resp1.status_code == 200
        assert resp1.json()["ai_score"] == 85.0
        assert mock_client.models.generate_content.call_count == 1

        # Second call without refresh returns cache
        resp2 = client.post(f"/api/jobs/{job_id}/results/{resume_id}/ai-review?refresh=false")
        assert resp2.status_code == 200
        assert resp2.json()["ai_score"] == 85.0
        assert mock_client.models.generate_content.call_count == 1  # Not called again!

        # Third call with refresh=true updates
        mock_response.text = json.dumps(mock_eval_2)
        resp3 = client.post(f"/api/jobs/{job_id}/results/{resume_id}/ai-review?refresh=true")
        assert resp3.status_code == 200
        assert resp3.json()["ai_score"] == 90.0
        assert mock_client.models.generate_content.call_count == 2
