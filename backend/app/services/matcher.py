import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from app.services.nlp import extract_skills

WEIGHTS = {"skill": 0.40, "semantic": 0.30, "experience": 0.15, "education": 0.10, "certification": 0.05}

def jd_profile(description: str) -> dict:
    skills = extract_skills(description)
    exp = 0.0
    m = re.search(r"(\d+(?:\.\d+)?)\s*\+?\s*years?", description, re.I)
    if m:
        exp = float(m.group(1))
    education = any(x in description.lower() for x in ["b.tech", "btech", "b.e", "bachelor", "m.tech", "master", "degree"])
    cert = any(x in description.lower() for x in ["certification", "certified", "certificate"])
    return {"skills": skills, "experience_years": exp, "education_required": education, "certification_required": cert}

def semantic_score(resume_text: str, jd_text: str) -> float:
    if not resume_text.strip() or not jd_text.strip():
        return 0.0
    vec = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), max_features=5000)
    matrix = vec.fit_transform([resume_text, jd_text])
    return float(cosine_similarity(matrix[0:1], matrix[1:2])[0][0] * 100)

def score_resume(parsed: dict, resume_text: str, jd_text: str) -> dict:
    jd = jd_profile(jd_text)
    required = {str(x).strip().lower() for x in jd["skills"]}
    candidate = {str(x).strip().lower() for x in parsed.get("skills", [])}
    skill = 100.0 if not required else len(required & candidate) / len(required) * 100
    semantic = semantic_score(resume_text, jd_text)
    req_exp = jd["experience_years"]
    cand_exp = float(parsed.get("experience_years", 0))
    experience = 100.0 if req_exp == 0 else min(cand_exp / req_exp * 100, 100)
    education = 100.0 if not jd["education_required"] else (100.0 if parsed.get("education") else 0.0)
    certification = 100.0 if not jd["certification_required"] else (100.0 if parsed.get("certifications") else 0.0)
    final = sum([
        skill * WEIGHTS["skill"], semantic * WEIGHTS["semantic"], experience * WEIGHTS["experience"],
        education * WEIGHTS["education"], certification * WEIGHTS["certification"]
    ])
    recommendation = "STRONG SHORTLIST" if final >= 85 else "SHORTLIST" if final >= 75 else "REVIEW" if final >= 60 else "LOW MATCH"
    return {
        "skill_score": round(skill, 2), "semantic_score": round(semantic, 2),
        "experience_score": round(experience, 2), "education_score": round(education, 2),
        "certification_score": round(certification, 2), "final_score": round(final, 2),
        "recommendation": recommendation, "required_skills": sorted(required),
        "matched_skills": sorted(required & candidate), "missing_skills": sorted(required - candidate)
    }
