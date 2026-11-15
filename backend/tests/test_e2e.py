import io
import pytest
from fastapi.testclient import TestClient
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import docx

from app.main import app

client = TestClient(app)


def generate_sample_pdf_resume() -> bytes:
    """Generates an in-memory PDF resume for end-to-end testing."""
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    p.drawString(100, 750, "Jane Doe")
    p.drawString(100, 735, "jane.doe@techcorp.io | +1 555-432-8765")
    p.drawString(100, 710, "Summary: Senior Python Full Stack Engineer with 6 years experience.")
    p.drawString(100, 690, "Skills: Python, FastAPI, Docker, PostgreSQL, React, AWS, TypeScript")
    p.drawString(100, 670, "Experience: Lead Developer at DataSystems from Jan 2019 to Present")
    p.drawString(100, 650, "Education: Bachelor of Science in Computer Science, 2018")
    p.drawString(100, 630, "Certifications: AWS Certified Solutions Architect")
    p.drawString(100, 610, "Projects: Built distributed ingestion engine handling 50k events/sec.")
    p.showPage()
    p.save()
    buffer.seek(0)
    return buffer.getvalue()


def generate_sample_docx_resume() -> bytes:
    """Generates an in-memory DOCX resume for end-to-end testing."""
    doc = docx.Document()
    doc.add_heading("Bob Smith", level=1)
    doc.add_paragraph("bob.smith@email.com | 555-876-5432")
    doc.add_paragraph("Summary: Junior Frontend Developer with 1 year experience.")
    doc.add_paragraph("Skills: HTML5, CSS3, JavaScript, jQuery")
    doc.add_paragraph("Experience: Web Intern at AgencyX from Jan 2023 to Dec 2023")
    doc.add_paragraph("Education: Associate Degree in Graphic Design")
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer.getvalue()


def test_full_pipeline_end_to_end():
    # 1. Create a Job Description
    jd_payload = {
        "title": "Senior Python & Cloud Engineer",
        "raw_text": """
        Job Title: Senior Python & Cloud Engineer
        Location: Remote

        Requirements:
        - 4+ years of software development experience
        - Must have: Python, FastAPI, Docker, PostgreSQL, AWS
        - Bachelor's degree in Computer Science or related field

        Nice to have:
        - React, TypeScript, Kubernetes
        """,
    }
    job_resp = client.post("/api/jobs", data=jd_payload)
    assert job_resp.status_code == 201, f"Failed creating job: {job_resp.text}"
    job_data = job_resp.json()
    job_id = job_data["id"]
    assert "Python" in job_data["required_skills"]
    assert "FastAPI" in job_data["required_skills"]

    # 2. Upload 2 generated test resumes (1 PDF, 1 DOCX)
    pdf_bytes = generate_sample_pdf_resume()
    docx_bytes = generate_sample_docx_resume()

    upload_files = [
        ("files", ("jane_doe_resume.pdf", pdf_bytes, "application/pdf")),
        ("files", ("bob_smith_resume.docx", docx_bytes, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")),
    ]
    upload_resp = client.post("/api/resumes/upload", files=upload_files)
    assert upload_resp.status_code == 200, f"Upload failed: {upload_resp.text}"
    batch_result = upload_resp.json()
    assert batch_result["total"] == 2
    assert batch_result["successful"] == 2
    assert batch_result["failed"] == 0

    jane_id = batch_result["results"][0]["resume_id"]
    bob_id = batch_result["results"][1]["resume_id"]
    assert jane_id is not None
    assert bob_id is not None

    # 3. Run Matching
    match_resp = client.post(f"/api/jobs/{job_id}/match")
    assert match_resp.status_code == 200, f"Match failed: {match_resp.text}"
    ranked = match_resp.json()
    assert len(ranked) >= 2

    # Verify Jane (Senior Python + Cloud) scores significantly higher and ranks above Bob (Junior Frontend)
    jane_result = next(r for r in ranked if r["resume_id"] == jane_id)
    bob_result = next(r for r in ranked if r["resume_id"] == bob_id)

    assert jane_result["overall_score"] > bob_result["overall_score"]
    assert jane_result["rank"] < bob_result["rank"]
    assert jane_result["overall_score"] >= 75.0
    assert "Python" in jane_result["matched_skills"]
    assert "FastAPI" in jane_result["matched_skills"]

    # 4. Fetch Results List
    results_resp = client.get(f"/api/jobs/{job_id}/results")
    assert results_resp.status_code == 200
    results_list = results_resp.json()
    assert len(results_list) == len(ranked)
    assert results_list[0]["rank"] == 1

    # 5. Fetch In-Depth Match Details for top candidate
    detail_resp = client.get(f"/api/jobs/{job_id}/results/{jane_id}")
    assert detail_resp.status_code == 200
    detail = detail_resp.json()
    assert detail["candidate"]["name"] == "Jane Doe"
    assert detail["overall_score"] == jane_result["overall_score"]
    assert "score_breakdown" in detail
    assert "skills" in detail["score_breakdown"]
    assert "experience" in detail["score_breakdown"]
    assert len(detail["reasons"]) > 0
    assert any("Python" in r or "skills" in r.lower() for r in detail["reasons"])


def test_delete_resume_with_matches_cascades_safely():
    """Verifies that deleting a resume with existing match_results succeeds without IntegrityError."""
    # 1. Create a job
    job_resp = client.post(
        "/api/jobs",
        data={"title": "Delete Test Job", "raw_text": "Python Developer needed with FastAPI experience"},
    )
    assert job_resp.status_code == 201
    job_id = job_resp.json()["id"]

    # 2. Upload a resume
    pdf_bytes = generate_sample_pdf_resume()
    upload_resp = client.post(
        "/api/resumes/upload",
        files=[("files", ("delete_candidate.pdf", pdf_bytes, "application/pdf"))],
    )
    assert upload_resp.status_code == 200
    resume_id = upload_resp.json()["results"][0]["resume_id"]

    # 3. Run match so match_results row is created
    match_resp = client.post(f"/api/jobs/{job_id}/match")
    assert match_resp.status_code == 200

    # 4. Delete the resume (must cascade cleanly without NOT NULL constraint failed on match_results.resume_id)
    del_resume_resp = client.delete(f"/api/resumes/{resume_id}")
    assert del_resume_resp.status_code == 200, f"Delete failed: {del_resume_resp.text}"
    assert del_resume_resp.json()["message"] == "Resume deleted successfully"

    # 5. Verify resume no longer exists
    get_res_resp = client.get(f"/api/resumes/{resume_id}")
    assert get_res_resp.status_code == 404

    # 6. Delete the job (must also cascade cleanly)
    del_job_resp = client.delete(f"/api/jobs/{job_id}")
    assert del_job_resp.status_code == 200
