from pathlib import Path
import csv, io
from uuid import uuid4
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.models import User, AuthSession, Job, Resume, Application
from app.schemas.schemas import *
from app.core.config import settings
from app.core.auth import hash_password, verify_password, create_session, current_user, require_role
from app.utils.parsers import extract_text
from app.services.nlp import parse_resume
from app.services.matcher import jd_profile, score_resume

router = APIRouter(prefix="/api")
UPLOAD_DIR = Path(__file__).resolve().parents[4] / "data" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

@router.get("/health")
def health(): return {"status":"ok","service":"AI Resume Scanner"}

# ---------- Authentication ----------
@router.post("/auth/register", response_model=LoginOut)
def register(payload: RegisterIn, db: Session = Depends(get_db)):
    email = payload.email.lower()
    if db.query(User).filter(User.email == email).first(): raise HTTPException(409, "Email already registered")
    user = User(name=payload.name, email=email, password_hash=hash_password(payload.password), role=payload.role)
    db.add(user); db.commit(); db.refresh(user)
    return {"token": create_session(user, db), "user": user}

@router.post("/auth/login", response_model=LoginOut)
def login(payload: LoginIn, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email.lower()).first()
    if not user or not verify_password(payload.password, user.password_hash): raise HTTPException(401, "Invalid email or password")
    return {"token": create_session(user, db), "user": user}

@router.get("/auth/me", response_model=UserOut)
def me(user: User = Depends(current_user)): return user

# ---------- Public/admin jobs ----------
@router.get("/jobs", response_model=list[JobOut])
def list_jobs(db: Session = Depends(get_db)): return db.query(Job).order_by(Job.created_at.desc()).all()

@router.get("/jobs/{job_id}", response_model=JobOut)
def get_job(job_id: int, db: Session = Depends(get_db)):
    job = db.get(Job, job_id)
    if not job: raise HTTPException(404, "Job not found")
    return job

@router.post("/jobs", response_model=JobOut)
def create_job(payload: JobCreate, db: Session = Depends(get_db), admin: User = Depends(require_role("admin"))):
    profile = jd_profile(payload.description)
    job = Job(title=payload.title, description=payload.description, required_skills=profile["skills"], created_by=admin.id)
    db.add(job); db.commit(); db.refresh(job); return job

@router.get("/admin/jobs", response_model=list[JobOut])
def admin_jobs(db: Session = Depends(get_db), admin: User = Depends(require_role("admin"))):
    return db.query(Job).filter((Job.created_by == admin.id) | (Job.created_by.is_(None))).order_by(Job.created_at.desc()).all()

# ---------- Legacy/admin screening upload ----------
@router.post("/jobs/{job_id}/resumes", response_model=list[ResumeOut])
async def upload_resumes(job_id: int, files: list[UploadFile] = File(...), db: Session = Depends(get_db), admin: User = Depends(require_role("admin"))):
    job = db.get(Job, job_id)
    if not job: raise HTTPException(404, "Job not found")
    results=[]
    for file in files:
        results.append(await _analyze_file(file, job, db, None))
    return results

async def _analyze_file(file: UploadFile, job: Job, db: Session, candidate_id: int | None):
    ext = Path(file.filename or "").suffix.lower()
    if ext not in {".pdf", ".docx"}: raise HTTPException(400, f"Unsupported file: {file.filename}")
    content = await file.read()
    if len(content) > settings.max_upload_mb * 1024 * 1024: raise HTTPException(413, f"{file.filename} exceeds upload limit")
    target = UPLOAD_DIR / f"{uuid4().hex}{ext}"; target.write_bytes(content)
    try: text = extract_text(str(target))
    except Exception as exc:
        target.unlink(missing_ok=True); raise HTTPException(400, f"Could not parse {file.filename}: {exc}")
    if not text.strip(): raise HTTPException(400, f"No readable text found in {file.filename}")
    parsed = parse_resume(text); scores = score_resume(parsed, text, job.description)
    parsed.update({"required_skills":scores["required_skills"],"matched_skills":scores["matched_skills"],"missing_skills":scores["missing_skills"]})
    resume = Resume(job_id=job.id,candidate_id=candidate_id,filename=file.filename,name=parsed["name"],email=parsed["email"],phone=parsed["phone"],raw_text=text,parsed_data=parsed,**{k:scores[k] for k in ["skill_score","semantic_score","experience_score","education_score","certification_score","final_score","recommendation"]})
    db.add(resume); db.commit(); db.refresh(resume); return resume

@router.get("/jobs/{job_id}/resumes", response_model=list[ResumeOut])
def list_resumes(job_id: int, db: Session = Depends(get_db), admin: User = Depends(require_role("admin"))):
    if not db.get(Job, job_id): raise HTTPException(404,"Job not found")
    return db.query(Resume).filter(Resume.job_id==job_id).order_by(Resume.final_score.desc()).all()

@router.get("/resumes/{resume_id}", response_model=ResumeOut)
def get_resume(resume_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    resume=db.get(Resume,resume_id)
    if not resume: raise HTTPException(404,"Resume not found")
    if user.role != "admin" and resume.candidate_id != user.id: raise HTTPException(403,"Access denied")
    return resume

# ---------- Candidate portal ----------
@router.get("/candidate/jobs", response_model=list[JobOut])
def candidate_jobs(db: Session = Depends(get_db), user: User = Depends(require_role("candidate"))):
    return db.query(Job).order_by(Job.created_at.desc()).all()

@router.post("/candidate/jobs/{job_id}/apply", response_model=CandidateApplicationOut)
async def apply(job_id: int, file: UploadFile = File(...), db: Session = Depends(get_db), candidate: User = Depends(require_role("candidate"))):
    job=db.get(Job,job_id)
    if not job: raise HTTPException(404,"Job not found")
    existing=db.query(Application).filter(Application.job_id==job_id,Application.candidate_id==candidate.id).first()
    if existing: raise HTTPException(409,"You have already applied for this job")
    resume=await _analyze_file(file,job,db,candidate.id)
    suggestions=[]
    pd=resume.parsed_data
    missing=pd.get("missing_skills",[])
    if missing: suggestions.append("Add evidence or projects demonstrating: " + ", ".join(missing) + ".")
    if resume.semantic_score < 50: suggestions.append("Tailor your professional summary and project descriptions to the job description using relevant terminology.")
    if resume.experience_score < 70: suggestions.append("Highlight measurable outcomes, internships, and relevant hands-on experience for this role.")
    if resume.education_score < 100: suggestions.append("Make your highest relevant degree and specialization easy to find near the top of the resume.")
    if resume.certification_score < 100: suggestions.append("Consider adding relevant certifications only when they genuinely support the target role.")
    if not suggestions: suggestions.append("Strong alignment. Keep the resume concise and continue adding measurable project outcomes.")
    app=Application(job_id=job.id,candidate_id=candidate.id,resume_id=resume.id,status="UNDER REVIEW",ai_suggestions=suggestions)
    db.add(app); db.commit(); db.refresh(app)
    return {"id":app.id,"status":app.status,"ai_suggestions":app.ai_suggestions,"applied_at":app.applied_at,"updated_at":app.updated_at,"job":job,"resume":resume}

@router.get("/candidate/applications", response_model=list[CandidateApplicationOut])
def candidate_applications(db: Session = Depends(get_db), candidate: User = Depends(require_role("candidate"))):
    apps=db.query(Application).filter(Application.candidate_id==candidate.id).order_by(Application.applied_at.desc()).all()
    return [{"id":a.id,"status":a.status,"ai_suggestions":a.ai_suggestions or [],"applied_at":a.applied_at,"updated_at":a.updated_at,"job":a.job,"resume":a.resume} for a in apps]

@router.get("/candidate/applications/{application_id}", response_model=CandidateApplicationOut)
def candidate_application(application_id:int,db:Session=Depends(get_db),candidate:User=Depends(require_role("candidate"))):
    a=db.get(Application,application_id)
    if not a or a.candidate_id!=candidate.id: raise HTTPException(404,"Application not found")
    return {"id":a.id,"status":a.status,"ai_suggestions":a.ai_suggestions or [],"applied_at":a.applied_at,"updated_at":a.updated_at,"job":a.job,"resume":a.resume}

# ---------- Admin applicant portal ----------
@router.get("/admin/applications", response_model=list[ApplicationOut])
def admin_applications(db:Session=Depends(get_db),admin:User=Depends(require_role("admin"))):
    jobs=db.query(Job).filter((Job.created_by==admin.id)|(Job.created_by.is_(None))).all(); ids=[j.id for j in jobs]
    apps=db.query(Application).filter(Application.job_id.in_(ids)).order_by(Application.updated_at.desc()).all() if ids else []
    return [{"id":a.id,"job_id":a.job_id,"candidate_id":a.candidate_id,"resume_id":a.resume_id,"status":a.status,"ai_suggestions":a.ai_suggestions or [],"applied_at":a.applied_at,"updated_at":a.updated_at,"job":a.job,"resume":a.resume,"candidate_name":a.candidate.name,"candidate_email":a.candidate.email} for a in apps]

@router.patch("/admin/applications/{application_id}/status", response_model=ApplicationOut)
def update_status(application_id:int,payload:StatusUpdate,db:Session=Depends(get_db),admin:User=Depends(require_role("admin"))):
    a=db.get(Application,application_id)
    if not a: raise HTTPException(404,"Application not found")
    if a.job.created_by not in (None, admin.id): raise HTTPException(403,"Access denied")
    a.status=payload.status; db.commit(); db.refresh(a)
    return {"id":a.id,"job_id":a.job_id,"candidate_id":a.candidate_id,"resume_id":a.resume_id,"status":a.status,"ai_suggestions":a.ai_suggestions or [],"applied_at":a.applied_at,"updated_at":a.updated_at,"job":a.job,"resume":a.resume,"candidate_name":a.candidate.name,"candidate_email":a.candidate.email}

@router.get("/admin/stats")
def admin_stats(db:Session=Depends(get_db),admin:User=Depends(require_role("admin"))):
    jobs=db.query(Job).filter((Job.created_by==admin.id)|(Job.created_by.is_(None))).all(); ids=[j.id for j in jobs]
    apps=db.query(Application).filter(Application.job_id.in_(ids)).all() if ids else []
    avg=round(sum(a.resume.final_score for a in apps)/len(apps),1) if apps else 0
    return {"jobs":len(jobs),"applications":len(apps),"shortlisted":sum(a.status in ["SHORTLISTED","INTERVIEW","HIRED"] for a in apps),"strong_matches":sum(a.resume.final_score>=85 for a in apps),"average_score":avg}

@router.get("/admin/reports.csv")
def report_csv(db:Session=Depends(get_db),admin:User=Depends(require_role("admin"))):
    apps=admin_applications(db,admin); output=io.StringIO(); w=csv.writer(output); w.writerow(["Candidate","Email","Job","Status","ATS Score","Skill Score","Semantic Score","Experience","Education","Certification","Recommendation","Missing Skills"])
    for a in apps:
        p=a["resume"].parsed_data or {}; w.writerow([a["candidate_name"],a["candidate_email"],a["job"].title,a["status"],a["resume"].final_score,a["resume"].skill_score,a["resume"].semantic_score,a["resume"].experience_score,a["resume"].education_score,a["resume"].certification_score,a["resume"].recommendation,", ".join(p.get("missing_skills",[]))])
    return StreamingResponse(iter([output.getvalue()]),media_type="text/csv",headers={"Content-Disposition":"attachment; filename=resume_screening_report.csv"})
