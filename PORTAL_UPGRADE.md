# AI Resume Scanner v2 — Two-Portal Upgrade

This version changes the application from a recruiter-only screening UI into a two-portal recruitment platform.

## Candidate Portal
- Candidate registration/login
- Browse published jobs
- Upload PDF/DOCX resume for a specific job
- Automatic AI analysis immediately after upload
- Application status tracking
- ATS/overall match score
- Skill, semantic, experience, education and certification scores
- Matched and missing skills
- Personalized AI resume-improvement suggestions

## Admin Portal
- Admin registration/login
- Dashboard statistics
- Publish jobs and define requirements through the job description
- View all applications
- See candidate identity/contact details
- See ATS score and all component scores
- See matched/missing skills and AI recommendation
- Change application status: Under Review, Shortlisted, Interview, Rejected, Hired
- Reports and CSV export

## Automatic analysis flow
Candidate -> selects job -> uploads resume -> FastAPI parses PDF/DOCX -> NLP extracts information -> matching engine scores resume -> Application + Resume analysis are saved -> admin sees the analyzed candidate automatically.

The AI analysis does not make the final hiring decision. Recruiters control the application status.

## Run
Backend:
```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload
```

Frontend:
```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`.

The backend performs a small automatic schema upgrade for the original v2 SQLite database, so existing jobs/resumes are retained. New authentication/application tables are created automatically.

For a clean test, create one Admin account and one Candidate account from the login page.
