import os
import sys
import glob

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

SAMPLE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "sample_data")
RESUMES_DIR = os.path.join(SAMPLE_DIR, "resumes")
JD_PATH = os.path.join(SAMPLE_DIR, "sample_jd.txt")


def run_pipeline():
    # 1. Read and create Job Description
    with open(JD_PATH, "r", encoding="utf-8") as f:
        jd_text = f.read()

    print("\n================== CREATING JOB DESCRIPTION ==================")
    job_resp = client.post(
        "/api/jobs",
        data={
            "title": "Java Spring Boot Developer",
            "raw_text": jd_text,
        },
    )
    assert job_resp.status_code == 201, f"Failed creating job: {job_resp.text}"
    job_data = job_resp.json()
    job_id = job_data["id"]
    print(f"Created Job ID: {job_id} - '{job_data['title']}'")
    print(f"Required Skills ({len(job_data['required_skills'])}): {job_data['required_skills']}")
    print(f"Preferred Skills ({len(job_data['preferred_skills'])}): {job_data['preferred_skills']}")
    print(f"Min Experience Required: {job_data['min_experience']} years")
    print(f"Education Requirements: {job_data['education']}")

    # 2. Upload all 12 resumes
    print("\n================== UPLOADING 12 RESUMES ==================")
    resume_files = sorted(glob.glob(os.path.join(RESUMES_DIR, "*.*")))
    upload_payload = []
    file_handles = []

    for filepath in resume_files:
        ext = os.path.splitext(filepath)[1].lower()
        if ext not in [".pdf", ".docx"]:
            continue
        fh = open(filepath, "rb")
        file_handles.append(fh)
        filename = os.path.basename(filepath)
        mime = "application/pdf" if ext == ".pdf" else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        upload_payload.append(("files", (filename, fh, mime)))

    try:
        upload_resp = client.post("/api/resumes/upload", files=upload_payload)
        assert upload_resp.status_code == 200, f"Upload failed: {upload_resp.text}"
        batch_summary = upload_resp.json()
        print(f"Total uploaded: {batch_summary['total']} | Success: {batch_summary['successful']} | Failed: {batch_summary['failed']}")
        uploaded_ids = {r["resume_id"] for r in batch_summary["results"] if r.get("resume_id")}
    finally:
        for fh in file_handles:
            fh.close()

    # 3. Inspect parsed data for each uploaded resume
    print("\n================== PARSED RESUME PROFILES ==================")
    resumes_resp = client.get("/api/resumes")
    all_resumes = resumes_resp.json()
    # Filter to only the 12 resumes we uploaded in this batch
    batch_resumes = [r for r in all_resumes if r["id"] in uploaded_ids]

    for r in batch_resumes:
        print(f"File: {r['filename']}")
        print(f"  Extracted Name: {r['name']}")
        print(f"  Extracted Exp:  {r['total_experience_years']} yrs")
        print(f"  Extracted Skills: {r['skills']}")
        print(f"  Extracted Edu:  {[e.get('degree') for e in r['education']]}")
        print("-" * 60)

    # 4. Run Matching
    print("\n================== RUNNING MATCHING ENGINE ==================")
    match_resp = client.post(f"/api/jobs/{job_id}/match")
    assert match_resp.status_code == 200, f"Match failed: {match_resp.text}"
    ranked_results = match_resp.json()

    # Filter to the current 12 resumes for clean ranking output
    current_results = [r for r in ranked_results if r["resume_id"] in uploaded_ids]
    # Re-sort and rank
    current_results.sort(key=lambda x: x["overall_score"], reverse=True)

    print("\n" + "=" * 90)
    print(f"{'RANK':<5} | {'CANDIDATE NAME':<18} | {'EXP (YRS)':<9} | {'SCORE':<7} | {'MATCHED SKILLS'}")
    print("=" * 90)
    for idx, item in enumerate(current_results, start=1):
        name_str = item["name"] or item["filename"]
        skills_str = ", ".join(item["matched_skills"]) if item["matched_skills"] else "None"
        exp_str = f"{item['total_experience_years']:.1f}"
        print(f"#{idx:<4} | {name_str:<18} | {exp_str:<9} | {item['overall_score']:<7.1f} | {skills_str}")
    print("=" * 90)

    # Print breakdown and reasons for top, middle, and bottom
    print("\n================== EXPLAINABILITY SAMPLES ==================")
    for sample_rank, sample_idx in [("Top Match (#1)", 0), ("Mid Match (#6)", 5), ("Bottom Match (#12)", -1)]:
        if abs(sample_idx) < len(current_results):
            cand = current_results[sample_idx]
            print(f"\n--- {sample_rank}: {cand['name']} ({cand['filename']}) ---")
            print(f"Overall Score: {cand['overall_score']}")
            print(f"Score Breakdown: {cand['score_breakdown']}")
            print(f"Matched Skills: {cand['matched_skills']}")
            print(f"Partially Matched: {cand['partially_matched_skills']}")
            print(f"Missing Skills: {cand['missing_skills']}")


if __name__ == "__main__":
    run_pipeline()
