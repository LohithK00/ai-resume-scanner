from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import inspect, text
from app.core.config import settings
from app.db.session import Base, engine
from app.models import User, AuthSession, Job, Resume, Application
from app.api.routes import router

# Create new tables and add the two nullable columns needed to upgrade the original v1 database.
Base.metadata.create_all(bind=engine)

def upgrade_existing_schema():
    inspector = inspect(engine)
    with engine.begin() as conn:
        job_cols = {c["name"] for c in inspector.get_columns("jobs")} if inspector.has_table("jobs") else set()
        resume_cols = {c["name"] for c in inspector.get_columns("resumes")} if inspector.has_table("resumes") else set()
        if "created_by" not in job_cols:
            conn.execute(text("ALTER TABLE jobs ADD COLUMN created_by INTEGER"))
        if "candidate_id" not in resume_cols:
            conn.execute(text("ALTER TABLE resumes ADD COLUMN candidate_id INTEGER"))

upgrade_existing_schema()
app = FastAPI(title=settings.app_name, version="2.0.0", description="AI-powered two-portal resume screening and candidate application platform")
app.add_middleware(CORSMiddleware, allow_origins=[x.strip() for x in settings.cors_origins.split(",")], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.include_router(router)

@app.get("/")
def root(): return {"message":"AI Resume Scanner API","docs":"/docs","portals":["candidate","admin"]}
