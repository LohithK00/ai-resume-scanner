from pydantic import BaseModel, Field, EmailStr
from datetime import datetime
from typing import Any

class RegisterIn(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    email: EmailStr
    password: str = Field(min_length=6, max_length=100)
    role: str = Field(default="candidate", pattern="^(candidate|admin)$")

class LoginIn(BaseModel):
    email: EmailStr
    password: str

class UserOut(BaseModel):
    id: int; name: str; email: EmailStr; role: str
    model_config = {"from_attributes": True}

class LoginOut(BaseModel):
    token: str
    user: UserOut

class JobCreate(BaseModel):
    title: str = Field(min_length=2, max_length=200)
    description: str = Field(min_length=20)

class JobOut(JobCreate):
    id: int
    required_skills: list[str] = []
    created_at: datetime
    model_config = {"from_attributes": True}

class StatusUpdate(BaseModel):
    status: str = Field(pattern="^(UNDER REVIEW|SHORTLISTED|INTERVIEW|REJECTED|HIRED)$")

class ResumeOut(BaseModel):
    id: int; job_id: int; filename: str; name: str; email: str | None; phone: str | None
    parsed_data: dict[str, Any]; skill_score: float; semantic_score: float; experience_score: float
    education_score: float; certification_score: float; final_score: float; recommendation: str
    model_config = {"from_attributes": True}

class ApplicationOut(BaseModel):
    id: int; job_id: int; candidate_id: int; resume_id: int; status: str
    ai_suggestions: list[str]; applied_at: datetime; updated_at: datetime
    job: JobOut; resume: ResumeOut
    candidate_name: str
    candidate_email: EmailStr

class CandidateApplicationOut(BaseModel):
    id: int; status: str; ai_suggestions: list[str]; applied_at: datetime; updated_at: datetime
    job: JobOut; resume: ResumeOut
