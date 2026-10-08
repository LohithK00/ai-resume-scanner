from pathlib import Path
import csv
import io
from uuid import uuid4

from fastapi import (
    APIRouter,
    Depends,
    File,
    UploadFile,
    HTTPException,
)
from fastapi.responses import StreamingResponse, FileResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.models import User, Job, Resume, Application
from app.schemas.schemas import *
from app.core.config import settings
from app.core.auth import (
    hash_password,
    verify_password,
    create_session,
    current_user,
    require_role,
)
from app.utils.parsers import extract_text
from app.services.nlp import parse_resume
from app.services.matcher import jd_profile, score_resume


router = APIRouter(prefix="/api")


# ============================================================
# FILE STORAGE
# ============================================================

# Project root:
# ai_resume_scanner/
# ├── backend/
# ├── frontend/
# └── data/
#
# routes.py:
# ai_resume_scanner/backend/app/api/routes.py
#
# parents[3] = ai_resume_scanner
PROJECT_ROOT = Path(__file__).resolve().parents[3]

# New/current upload location
UPLOAD_DIR = PROJECT_ROOT / "data" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Legacy location used by the earlier version of the project.
# This allows previously uploaded resumes to continue working.
LEGACY_UPLOAD_DIR = PROJECT_ROOT.parent / "data" / "uploads"


# ============================================================
# HEALTH
# ============================================================

@router.get("/health")
def health():
    return {
        "status": "ok",
        "service": "AI Resume Scanner",
    }


# ============================================================
# AUTHENTICATION
# ============================================================

@router.post("/auth/register", response_model=LoginOut)
def register(
    payload: RegisterIn,
    db: Session = Depends(get_db),
):
    email = payload.email.lower()

    if db.query(User).filter(User.email == email).first():
        raise HTTPException(
            status_code=409,
            detail="Email already registered",
        )

    user = User(
        name=payload.name,
        email=email,
        password_hash=hash_password(payload.password),
        role=payload.role,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return {
        "token": create_session(user, db),
        "user": user,
    }


@router.post("/auth/login", response_model=LoginOut)
def login(
    payload: LoginIn,
    db: Session = Depends(get_db),
):
    user = (
        db.query(User)
        .filter(User.email == payload.email.lower())
        .first()
    )

    if not user or not verify_password(
        payload.password,
        user.password_hash,
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password",
        )

    return {
        "token": create_session(user, db),
        "user": user,
    }


@router.get("/auth/me", response_model=UserOut)
def me(
    user: User = Depends(current_user),
):
    return user


# ============================================================
# JOBS
# ============================================================

@router.get("/jobs", response_model=list[JobOut])
def list_jobs(
    db: Session = Depends(get_db),
):
    return (
        db.query(Job)
        .order_by(Job.created_at.desc())
        .all()
    )


@router.get("/jobs/{job_id}", response_model=JobOut)
def get_job(
    job_id: int,
    db: Session = Depends(get_db),
):
    job = db.get(Job, job_id)

    if not job:
        raise HTTPException(
            status_code=404,
            detail="Job not found",
        )

    return job


@router.post("/jobs", response_model=JobOut)
def create_job(
    payload: JobCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_role("admin")),
):
    profile = jd_profile(payload.description)

    job = Job(
        title=payload.title,
        description=payload.description,
        required_skills=profile["skills"],
        created_by=admin.id,
    )

    db.add(job)
    db.commit()
    db.refresh(job)

    return job


@router.get("/admin/jobs", response_model=list[JobOut])
def admin_jobs(
    db: Session = Depends(get_db),
    admin: User = Depends(require_role("admin")),
):
    return (
        db.query(Job)
        .filter(
            (Job.created_by == admin.id)
            | (Job.created_by.is_(None))
        )
        .order_by(Job.created_at.desc())
        .all()
    )


# ============================================================
# RESUME ANALYSIS
# ============================================================

@router.post(
    "/jobs/{job_id}/resumes",
    response_model=list[ResumeOut],
)
async def upload_resumes(
    job_id: int,
    files: list[UploadFile] = File(...),
    db: Session = Depends(get_db),
    admin: User = Depends(require_role("admin")),
):
    job = db.get(Job, job_id)

    if not job:
        raise HTTPException(
            status_code=404,
            detail="Job not found",
        )

    # Prevent an admin from uploading to another admin's job.
    if job.created_by not in (None, admin.id):
        raise HTTPException(
            status_code=403,
            detail="Access denied",
        )

    results = []

    for file in files:
        results.append(
            await _analyze_file(
                file,
                job,
                db,
                None,
            )
        )

    return results


async def _analyze_file(
    file: UploadFile,
    job: Job,
    db: Session,
    candidate_id: int | None,
):
    original_filename = file.filename or "resume"

    ext = Path(original_filename).suffix.lower()

    if ext not in {".pdf", ".docx"}:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file: {original_filename}",
        )

    content = await file.read()

    if len(content) > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(
            status_code=413,
            detail=(
                f"{original_filename} exceeds "
                f"the {settings.max_upload_mb} MB upload limit"
            ),
        )

    # Generate a private storage filename.
    stored_filename = f"{uuid4().hex}{ext}"

    target = UPLOAD_DIR / stored_filename

    target.write_bytes(content)

    try:
        text = extract_text(str(target))

    except Exception as exc:
        target.unlink(missing_ok=True)

        raise HTTPException(
            status_code=400,
            detail=(
                f"Could not parse "
                f"{original_filename}: {exc}"
            ),
        )

    if not text.strip():
        target.unlink(missing_ok=True)

        raise HTTPException(
            status_code=400,
            detail=(
                f"No readable text found in "
                f"{original_filename}"
            ),
        )

    parsed = parse_resume(
        text
    )

    scores = score_resume(
        parsed,
        text,
        job.description,
    )

    parsed.update(
        {
            "required_skills": scores["required_skills"],
            "matched_skills": scores["matched_skills"],
            "missing_skills": scores["missing_skills"],
        }
    )

    resume = Resume(
        job_id=job.id,
        candidate_id=candidate_id,
        filename=original_filename,

        # IMPORTANT:
        # This is the private generated filename,
        # not a public URL.
        file_path=stored_filename,

        name=parsed["name"],
        email=parsed["email"],
        phone=parsed["phone"],
        raw_text=text,
        parsed_data=parsed,

        **{
            key: scores[key]
            for key in [
                "skill_score",
                "semantic_score",
                "experience_score",
                "education_score",
                "certification_score",
                "final_score",
                "recommendation",
            ]
        },
    )

    db.add(resume)
    db.commit()
    db.refresh(resume)

    return resume


@router.get(
    "/jobs/{job_id}/resumes",
    response_model=list[ResumeOut],
)
def list_resumes(
    job_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_role("admin")),
):
    job = db.get(Job, job_id)

    if not job:
        raise HTTPException(
            status_code=404,
            detail="Job not found",
        )

    if job.created_by not in (None, admin.id):
        raise HTTPException(
            status_code=403,
            detail="Access denied",
        )

    return (
        db.query(Resume)
        .filter(Resume.job_id == job_id)
        .order_by(Resume.final_score.desc())
        .all()
    )


@router.get(
    "/resumes/{resume_id}",
    response_model=ResumeOut,
)
def get_resume(
    resume_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    resume = db.get(
        Resume,
        resume_id,
    )

    if not resume:
        raise HTTPException(
            status_code=404,
            detail="Resume not found",
        )

    if (
        user.role != "admin"
        and resume.candidate_id != user.id
    ):
        raise HTTPException(
            status_code=403,
            detail="Access denied",
        )

    return resume


# ============================================================
# SECURE ADMIN RESUME VIEWER
# ============================================================

@router.get("/admin/resumes/{resume_id}/file")
def admin_resume_file(
    resume_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_role("admin")),
):
    """
    Securely returns the original uploaded resume.

    Only an authenticated admin can access this endpoint.
    The admin must also own the job associated with the resume.
    """

    resume = db.get(
        Resume,
        resume_id,
    )

    if not resume:
        raise HTTPException(
            status_code=404,
            detail="Resume not found",
        )

    job = db.get(
        Job,
        resume.job_id,
    )

    if not job:
        raise HTTPException(
            status_code=404,
            detail="Associated job not found",
        )

    # Admin can only access resumes belonging to:
    # 1. Their own jobs
    # 2. Legacy jobs with no owner
    if job.created_by not in (None, admin.id):
        raise HTTPException(
            status_code=403,
            detail="Access denied",
        )

    if not resume.file_path:
        raise HTTPException(
            status_code=404,
            detail=(
                "Original resume file is not available "
                "for this application"
            ),
        )

    # --------------------------------------------------------
    # SECURITY:
    # Never allow file_path to escape the upload directory.
    # --------------------------------------------------------

    requested_name = Path(
        resume.file_path
    ).name

    if requested_name != resume.file_path:
        raise HTTPException(
            status_code=400,
            detail="Invalid resume file path",
        )

    # First look in the new/current upload directory.
    target = (
        UPLOAD_DIR / requested_name
    ).resolve()

    upload_root = UPLOAD_DIR.resolve()

    if upload_root not in target.parents:
        raise HTTPException(
            status_code=400,
            detail="Invalid resume file path",
        )

    # --------------------------------------------------------
    # Backward compatibility:
    # Existing versions of the project may have stored files
    # in the legacy upload directory.
    # --------------------------------------------------------

    if not target.exists():

        legacy_root = LEGACY_UPLOAD_DIR.resolve()

        legacy_target = (
            LEGACY_UPLOAD_DIR / requested_name
        ).resolve()

        if (
            legacy_root in legacy_target.parents
            and legacy_target.exists()
        ):
            target = legacy_target

    if not target.exists():
        raise HTTPException(
            status_code=404,
            detail="Resume file no longer exists",
        )

    extension = target.suffix.lower()

    media_types = {
        ".pdf": "application/pdf",
        ".docx": (
            "application/"
            "vnd.openxmlformats-officedocument."
            "wordprocessingml.document"
        ),
    }

    media_type = media_types.get(
        extension,
        "application/octet-stream",
    )

    return FileResponse(
        path=str(target),
        media_type=media_type,
        filename=resume.filename,
        headers={
            "Content-Disposition": (
                f'inline; filename="{resume.filename}"'
            )
        },
    )


# ============================================================
# CANDIDATE PORTAL
# ============================================================

@router.get(
    "/candidate/jobs",
    response_model=list[JobOut],
)
def candidate_jobs(
    db: Session = Depends(get_db),
    user: User = Depends(require_role("candidate")),
):
    return (
        db.query(Job)
        .order_by(Job.created_at.desc())
        .all()
    )


@router.post(
    "/candidate/jobs/{job_id}/apply",
    response_model=CandidateApplicationOut,
)
async def apply(
    job_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    candidate: User = Depends(require_role("candidate")),
):
    job = db.get(
        Job,
        job_id,
    )

    if not job:
        raise HTTPException(
            status_code=404,
            detail="Job not found",
        )

    existing = (
        db.query(Application)
        .filter(
            Application.job_id == job_id,
            Application.candidate_id == candidate.id,
        )
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=409,
            detail="You have already applied for this job",
        )

    # Automatic resume analysis.
    resume = await _analyze_file(
        file,
        job,
        db,
        candidate.id,
    )

    suggestions = []

    parsed_data = resume.parsed_data

    missing = parsed_data.get(
        "missing_skills",
        [],
    )

    if missing:
        suggestions.append(
            "Add evidence or projects demonstrating: "
            + ", ".join(missing)
            + "."
        )

    if resume.semantic_score < 50:
        suggestions.append(
            "Tailor your professional summary and "
            "project descriptions to the job description "
            "using relevant terminology."
        )

    if resume.experience_score < 70:
        suggestions.append(
            "Highlight measurable outcomes, internships, "
            "and relevant hands-on experience for this role."
        )

    if resume.education_score < 100:
        suggestions.append(
            "Make your highest relevant degree and "
            "specialization easy to find near the top "
            "of the resume."
        )

    if resume.certification_score < 100:
        suggestions.append(
            "Consider adding relevant certifications only "
            "when they genuinely support the target role."
        )

    if not suggestions:
        suggestions.append(
            "Strong alignment. Keep the resume concise "
            "and continue adding measurable project outcomes."
        )

    application = Application(
        job_id=job.id,
        candidate_id=candidate.id,
        resume_id=resume.id,
        status="UNDER REVIEW",
        ai_suggestions=suggestions,
    )

    db.add(application)
    db.commit()
    db.refresh(application)

    return {
        "id": application.id,
        "status": application.status,
        "ai_suggestions": application.ai_suggestions,
        "applied_at": application.applied_at,
        "updated_at": application.updated_at,
        "job": job,
        "resume": resume,
    }


@router.get(
    "/candidate/applications",
    response_model=list[CandidateApplicationOut],
)
def candidate_applications(
    db: Session = Depends(get_db),
    candidate: User = Depends(require_role("candidate")),
):
    applications = (
        db.query(Application)
        .filter(
            Application.candidate_id == candidate.id
        )
        .order_by(
            Application.applied_at.desc()
        )
        .all()
    )

    return [
        {
            "id": application.id,
            "status": application.status,
            "ai_suggestions": (
                application.ai_suggestions or []
            ),
            "applied_at": application.applied_at,
            "updated_at": application.updated_at,
            "job": application.job,
            "resume": application.resume,
        }
        for application in applications
    ]


@router.get(
    "/candidate/applications/{application_id}",
    response_model=CandidateApplicationOut,
)
def candidate_application(
    application_id: int,
    db: Session = Depends(get_db),
    candidate: User = Depends(require_role("candidate")),
):
    application = db.get(
        Application,
        application_id,
    )

    if (
        not application
        or application.candidate_id != candidate.id
    ):
        raise HTTPException(
            status_code=404,
            detail="Application not found",
        )

    return {
        "id": application.id,
        "status": application.status,
        "ai_suggestions": (
            application.ai_suggestions or []
        ),
        "applied_at": application.applied_at,
        "updated_at": application.updated_at,
        "job": application.job,
        "resume": application.resume,
    }


# ============================================================
# ADMIN APPLICANT PORTAL
# ============================================================

@router.get(
    "/admin/applications",
    response_model=list[ApplicationOut],
)
def admin_applications(
    db: Session = Depends(get_db),
    admin: User = Depends(require_role("admin")),
):
    jobs = (
        db.query(Job)
        .filter(
            (Job.created_by == admin.id)
            | (Job.created_by.is_(None))
        )
        .all()
    )

    job_ids = [
        job.id
        for job in jobs
    ]

    if not job_ids:
        return []

    applications = (
        db.query(Application)
        .filter(
            Application.job_id.in_(job_ids)
        )
        .order_by(
            Application.updated_at.desc()
        )
        .all()
    )

    return [
        {
            "id": application.id,
            "job_id": application.job_id,
            "candidate_id": application.candidate_id,
            "resume_id": application.resume_id,
            "status": application.status,
            "ai_suggestions": (
                application.ai_suggestions or []
            ),
            "applied_at": application.applied_at,
            "updated_at": application.updated_at,
            "job": application.job,
            "resume": application.resume,
            "candidate_name": application.candidate.name,
            "candidate_email": application.candidate.email,
        }
        for application in applications
    ]


@router.patch(
    "/admin/applications/{application_id}/status",
    response_model=ApplicationOut,
)
def update_status(
    application_id: int,
    payload: StatusUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_role("admin")),
):
    application = db.get(
        Application,
        application_id,
    )

    if not application:
        raise HTTPException(
            status_code=404,
            detail="Application not found",
        )

    if application.job.created_by not in (
        None,
        admin.id,
    ):
        raise HTTPException(
            status_code=403,
            detail="Access denied",
        )

    application.status = payload.status

    db.commit()
    db.refresh(application)

    return {
        "id": application.id,
        "job_id": application.job_id,
        "candidate_id": application.candidate_id,
        "resume_id": application.resume_id,
        "status": application.status,
        "ai_suggestions": (
            application.ai_suggestions or []
        ),
        "applied_at": application.applied_at,
        "updated_at": application.updated_at,
        "job": application.job,
        "resume": application.resume,
        "candidate_name": application.candidate.name,
        "candidate_email": application.candidate.email,
    }


# ============================================================
# ADMIN STATISTICS
# ============================================================

@router.get("/admin/stats")
def admin_stats(
    db: Session = Depends(get_db),
    admin: User = Depends(require_role("admin")),
):
    jobs = (
        db.query(Job)
        .filter(
            (Job.created_by == admin.id)
            | (Job.created_by.is_(None))
        )
        .all()
    )

    job_ids = [
        job.id
        for job in jobs
    ]

    applications = (
        db.query(Application)
        .filter(
            Application.job_id.in_(job_ids)
        )
        .all()
        if job_ids
        else []
    )

    average_score = (
        round(
            sum(
                application.resume.final_score
                for application in applications
            )
            / len(applications),
            1,
        )
        if applications
        else 0
    )

    return {
        "jobs": len(jobs),
        "applications": len(applications),
        "shortlisted": sum(
            application.status
            in [
                "SHORTLISTED",
                "INTERVIEW",
                "HIRED",
            ]
            for application in applications
        ),
        "strong_matches": sum(
            application.resume.final_score >= 85
            for application in applications
        ),
        "average_score": average_score,
    }


# ============================================================
# ADMIN CSV REPORT
# ============================================================

@router.get("/admin/reports.csv")
def report_csv(
    db: Session = Depends(get_db),
    admin: User = Depends(require_role("admin")),
):
    applications = admin_applications(
        db,
        admin,
    )

    output = io.StringIO()

    writer = csv.writer(output)

    writer.writerow(
        [
            "Candidate",
            "Email",
            "Job",
            "Status",
            "ATS Score",
            "Skill Score",
            "Semantic Score",
            "Experience",
            "Education",
            "Certification",
            "Recommendation",
            "Missing Skills",
        ]
    )

    for application in applications:

        resume = application["resume"]

        parsed_data = (
            resume.parsed_data or {}
        )

        writer.writerow(
            [
                application["candidate_name"],
                application["candidate_email"],
                application["job"].title,
                application["status"],
                resume.final_score,
                resume.skill_score,
                resume.semantic_score,
                resume.experience_score,
                resume.education_score,
                resume.certification_score,
                resume.recommendation,
                ", ".join(
                    parsed_data.get(
                        "missing_skills",
                        [],
                    )
                ),
            ]
        )

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": (
                "attachment; "
                "filename=resume_screening_report.csv"
            )
        },
    )