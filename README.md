# AI-Powered Resume Screening and Candidate Shortlisting System

A college-ready BTech CSE mini project that parses PDF/DOCX resumes, extracts job-relevant information, compares candidates against a job description, calculates an explainable match score, and ranks candidates.

## Features

- PDF and DOCX resume parsing
- Candidate name, email, phone, skills, education, experience and certification extraction
- Job-description skill extraction
- Explainable scoring engine
- TF-IDF + cosine similarity for semantic-style text matching
- Skill match and missing-skill analysis
- Candidate ranking and recommendation
- Recruiter dashboard
- Job statistics endpoint
- CSV candidate report export
- SQLite for local development / PostgreSQL for deployment
- Docker Compose support
- No paid AI API required

## Score model

| Factor | Weight |
|---|---:|
| Skill Match | 40% |
| Text Similarity | 30% |
| Experience | 15% |
| Education | 10% |
| Certification | 5% |

Recommendations:

- 85–100: STRONG SHORTLIST
- 75–84.99: SHORTLIST
- 60–74.99: REVIEW
- Below 60: LOW MATCH

## Run locally

### Backend

```bash
cd backend
python -m venv .venv
# macOS/Linux
source .venv/bin/activate
# Windows PowerShell: .venv\\Scripts\\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

API: http://localhost:8000  
Swagger: http://localhost:8000/docs

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open the Vite URL shown in the terminal. By default the frontend expects `http://localhost:8000/api`.

## Docker

```bash
docker compose up --build
```

## API flow

1. `POST /api/jobs` — create a job profile.
2. `POST /api/jobs/{job_id}/resumes` — upload one or more PDF/DOCX resumes.
3. `GET /api/jobs/{job_id}/resumes` — retrieve ranked candidates.
4. `GET /api/jobs/{job_id}/stats` — retrieve dashboard statistics.
5. `GET /api/jobs/{job_id}/export.csv` — export a recruiter report.

## Academic note

This system is designed as an educational prototype. It should support recruiter review rather than make irreversible employment decisions automatically. It deliberately excludes sensitive personal attributes from scoring.
