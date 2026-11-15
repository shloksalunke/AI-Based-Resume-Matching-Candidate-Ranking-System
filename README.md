# AI Resume Matching & Candidate Ranking System

An explainable recruitment tool that compares a Job Description (JD) against a batch of resumes and produces a 0–100 match score, a ranked candidate list, and a skill-gap analysis for every candidate.

The scoring engine is deterministic and runs fully offline. It combines rule-based parsing, a skills taxonomy, and sentence embeddings. No paid API or external service is required.

---

## Table of Contents

1. [Features](#features)
2. [Architecture](#architecture)
3. [Matching Algorithm](#matching-algorithm)
4. [Tech Stack](#tech-stack)
5. [Project Structure](#project-structure)
6. [Getting Started](#getting-started)
7. [Configuration](#configuration)
8. [API Reference](#api-reference)
9. [Sample Data](#sample-data)
10. [Testing](#testing)
11. [Limitations & Future Work](#limitations--future-work)

---

## Features

- **Job Description input**: paste text or upload PDF, DOCX or TXT. The system extracts core, required and preferred skills, minimum experience and education.
- **Batch resume upload**: upload 10 or more PDF and DOCX resumes at once. Each file is reported individually, so one bad file does not fail the batch.
- **Resume parsing**: name, email, phone, skills, total experience, companies and designations, education, certifications and projects.
- **AI matching**: 0–100 score per candidate using exact, alias and semantic matching rather than keyword counting alone.
- **Ranking dashboard**: sortable table with experience, match percentage and matched skills, plus a minimum-score filter.
- **Candidate analysis**: extracted profile, score gauge, five-component breakdown, matched, partial and missing skills, experience comparison, and a plain-language "Why this score?" list.
- **Candidate comparison**: side-by-side view of up to three candidates.

---

## Architecture

<p align="center">
  <img src="docs/architecture.png" alt="System Architecture" width="100%" />
</p>

**Request flow**

1. The recruiter creates a job and uploads resumes in the React frontend.
2. The frontend calls the FastAPI REST API.
3. The JD parser and resume parser turn raw text into structured data.
4. Skills are extracted using the skills taxonomy and spaCy, and text is embedded with MiniLM.
5. Parsed jobs and resumes are stored in the database through SQLAlchemy.
6. The matching engine scores every resume against the selected job.
7. Scores, breakdowns and reasons are saved with the match results.
8. Ranked results are returned to the frontend and shown in the dashboard.

Routes stay thin. All business logic lives in the `services/` layer.

---

## Matching Algorithm

The overall score is the sum of five components:

| Component | Max points | What it measures |
| :--- | :---: | :--- |
| Skills | 40 | Weighted overlap between JD skills and candidate skills |
| Semantic similarity | 25 | Embedding similarity of the full JD and full resume |
| Experience | 20 | Candidate years against the required years, discounted by skill relevance |
| Education | 10 | Degree level against the JD requirement |
| Relevance | 5 | Projects and certifications |

### Skills (40)

Skills are weighted by how important they are in the JD:

| Tier | Weight | How it is detected |
| :--- | :---: | :--- |
| Core | 3x | Appears in the job title, is mentioned three or more times, or is among the first two required skills |
| Required | 2x | Listed under "Requirements" or "Must have" |
| Preferred | 1x | Listed under "Nice to have" or "Bonus" |

Match types:

- **Exact or alias match** earns full credit. Aliases come from `skills_taxonomy.json` (for example `k8s` maps to `Kubernetes`).
- **Semantic match** earns half credit when embedding cosine similarity is 0.75 or higher. It is applied only between skills in the same taxonomy category, and a blocklist prevents known false positives such as Java and JavaScript.
- Generic skills such as Git, Agile and Communication are excluded from the required-skill ratio unless the JD lists them explicitly.

### Semantic similarity (25)

The full JD and full resume are encoded with `all-MiniLM-L6-v2` and compared with cosine similarity. Because unrelated resumes still share generic vocabulary, the value is calibrated:

```
calibrated = clamp((cosine - 0.25) / (1 - 0.25), 0, 1)
semantic_points = calibrated * 25
```

### Experience (20)

```
base = min(1, candidate_years / required_years) * 20
blended_ratio = 0.6 * core_skill_ratio + 0.4 * required_skill_ratio
experience_points = base * max(0.25, blended_ratio)
```

The discount stops a senior candidate from an unrelated stack from earning full experience points. Total years are computed from merged, non-overlapping date ranges and explicit phrases such as "5 years of experience". Education dates are ignored.

### Education (10) and Relevance (5)

Education awards full points when the degree level meets or exceeds the JD, partial points for a lower level, and a small baseline when no degree is found. Relevance awards points for listed projects and certifications.

### Core-skill gate

If a candidate matches none of the JD's core skills, the overall score is capped at 30 and the reason is recorded, for example:

```
Capped: none of the core skills (Java, Spring Boot) found
```

This keeps candidates from adjacent stacks from outranking candidates who have the role's primary skills.

### Explainability

Every result includes the points per component, matched, partial and missing skills, and a list of human-readable reasons, for example `Matched 7/9 required skills` or `Experience discounted: core skills 2/2, required skills 3/7`.

---

## Tech Stack

| Layer | Technologies |
| :--- | :--- |
| Frontend | React 19, TypeScript (strict), Vite, Tailwind CSS, React Router, TanStack Query, Axios, Recharts |
| Backend | Python 3.11, FastAPI, SQLAlchemy 2.0, Pydantic v2, Uvicorn |
| AI / NLP | sentence-transformers (`all-MiniLM-L6-v2`), spaCy (`en_core_web_sm`), scikit-learn, NumPy |
| File parsing | pdfplumber, python-docx |
| Database | SQLite by default, PostgreSQL through `DATABASE_URL` |
| Testing | pytest |

---

## Project Structure

```
resume-matcher/
├── README.md
├── docs/
│   └── architecture.png
├── backend/
│   ├── requirements.txt
│   ├── .env.example
│   ├── sample_data/
│   │   ├── sample_jd.txt
│   │   └── resumes/
│   ├── scripts/
│   │   ├── generate_sample_resumes.py
│   │   └── run_sample_matching.py
│   ├── tests/
│   └── app/
│       ├── main.py
│       ├── core/          # configuration, database
│       ├── models/        # SQLAlchemy models
│       ├── schemas/       # Pydantic schemas
│       ├── api/routes/    # health, jobs, resumes, matching
│       ├── services/      # parser, jd, embedding, matching
│       └── data/
│           └── skills_taxonomy.json
└── frontend/
    ├── .env.example
    └── src/
        ├── api/
        ├── components/
        ├── hooks/
        ├── pages/
        ├── types/
        └── utils/
```

---

## Getting Started

### Prerequisites

- Python 3.10 or newer
- Node.js 18 or newer

### Backend

Windows (PowerShell):

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m spacy download en_core_web_sm
copy .env.example .env
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

macOS / Linux:

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm
cp .env.example .env
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

The API runs at `http://127.0.0.1:8000` and interactive docs are at `http://127.0.0.1:8000/docs`.

The first matching run downloads the MiniLM model (about 90 MB). After that, the system works offline.

### Frontend

In a second terminal:

```bash
cd frontend
npm install
cp .env.example .env      # on Windows PowerShell: copy .env.example .env
npm run dev
```

The app runs at `http://localhost:5173`.

### Quick walkthrough

1. Open the app and choose **New Job**.
2. Paste the contents of `backend/sample_data/sample_jd.txt`.
3. Open the job and upload all files from `backend/sample_data/resumes/`.
4. Click **Run Matching**.
5. Review the ranking, open a candidate for the detailed analysis, and select two or three candidates to compare.

---

## Configuration

### Backend (`backend/.env`)

| Variable | Default | Description |
| :--- | :--- | :--- |
| `APP_NAME` | `Resume Matching API` | Application name |
| `APP_ENV` | `development` | Environment name |
| `DEBUG` | `True` | Debug mode |
| `API_V1_PREFIX` | `/api` | API route prefix |
| `DATABASE_URL` | `sqlite:///./resume_matcher.db` | SQLAlchemy connection string |
| `ALLOWED_ORIGINS` | `http://localhost:5173,http://127.0.0.1:5173` | Allowed CORS origins |
| `UPLOAD_DIR` | `./uploads` | Upload directory |
| `MAX_FILE_SIZE_MB` | `5` | Maximum size per uploaded file |

### Frontend (`frontend/.env`)

| Variable | Default | Description |
| :--- | :--- | :--- |
| `VITE_API_URL` | `http://127.0.0.1:8000` | Backend base URL |

To use PostgreSQL, install `psycopg2-binary` and set `DATABASE_URL`, for example `postgresql+psycopg2://user:password@localhost:5432/resume_matcher`.

---

## API Reference

All endpoints are prefixed with `/api`.

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| GET | `/health` | Service and database health check |
| POST | `/jobs` | Create a job from pasted text or an uploaded file |
| GET | `/jobs` | List jobs |
| GET | `/jobs/{job_id}` | Get a job with its extracted requirements |
| DELETE | `/jobs/{job_id}` | Delete a job and its match results |
| POST | `/resumes/upload` | Upload and parse multiple resumes (PDF or DOCX) |
| GET | `/resumes` | List parsed resumes |
| GET | `/resumes/{resume_id}` | Get a parsed resume |
| DELETE | `/resumes/{resume_id}` | Delete a resume and its match results |
| POST | `/jobs/{job_id}/match` | Score all resumes against a job and return the ranking |
| GET | `/jobs/{job_id}/results` | Ranked results for a job |
| GET | `/jobs/{job_id}/results/{resume_id}` | Detailed analysis for one candidate |

---

## Sample Data

All sample data is synthetic. No real personal information is used.

- `backend/sample_data/sample_jd.txt` is a Java Spring Boot Developer JD.
- `backend/sample_data/resumes/` holds 12 generated resumes (7 PDF, 5 DOCX) covering strong, partial, unrelated and fresher profiles.

To regenerate the resumes or run matching from the command line:

```bash
cd backend
python scripts/generate_sample_resumes.py
python scripts/run_sample_matching.py
```

---

## Testing

```bash
# Backend
cd backend
pytest -v

# Frontend type check and production build
cd frontend
npm run build
```

The backend suite covers resume parsing, JD parsing, the matching service (including the core-skill gate and false-positive handling), and an end-to-end upload-to-ranking flow.

---

## Limitations & Future Work

**Current limitations**

- Parsing is rule-based. Unusual resume layouts can reduce extraction accuracy.
- Scanned or image-only PDFs are not supported because there is no OCR step.
- Skill detection depends on taxonomy coverage. Skills outside the taxonomy are not recognized.
- MiniLM can be less reliable on very short strings, which is why skill-level semantic matching is restricted by category.
- Authentication is intentionally out of scope for this MVP.

**Possible improvements**

- OCR for scanned resumes.
- Larger taxonomy and automatic skill discovery from the JD.
- Fine-tuned or larger embedding models.
- Optional LLM re-ranking as a separate layer that never changes the deterministic score.
- JWT authentication and multi-recruiter workspaces.
- Docker packaging and PostgreSQL deployment.
