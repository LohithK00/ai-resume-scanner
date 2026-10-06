import re
from collections import defaultdict

SKILL_ALIASES = {
    "python": ["python"], "java": ["java"], "c++": ["c++", "cpp"], "javascript": ["javascript", "js"],
    "typescript": ["typescript", "ts"], "sql": ["sql"], "postgresql": ["postgresql", "postgres"],
    "mysql": ["mysql"], "mongodb": ["mongodb", "mongo db"], "react": ["react", "react.js"],
    "node.js": ["node.js", "nodejs", "node js"], "flask": ["flask"], "fastapi": ["fastapi"],
    "django": ["django"], "machine learning": ["machine learning", "ml"], "deep learning": ["deep learning", "dl"],
    "nlp": ["nlp", "natural language processing"], "tensorflow": ["tensorflow"], "pytorch": ["pytorch"],
    "scikit-learn": ["scikit-learn", "sklearn"], "opencv": ["opencv", "open cv"], "git": ["git"],
    "docker": ["docker"], "kubernetes": ["kubernetes", "k8s"], "aws": ["aws", "amazon web services"],
    "azure": ["azure"], "gcp": ["gcp", "google cloud"], "rest api": ["rest api", "restful api"],
    "linux": ["linux"], "pandas": ["pandas"], "numpy": ["numpy"], "llm": ["llm", "large language model"],
    "rag": ["rag", "retrieval augmented generation"], "power bi": ["power bi"], "excel": ["excel"],
}

def _contains(text: str, term: str) -> bool:
    return re.search(r"(?<![a-z0-9])" + re.escape(term) + r"(?![a-z0-9])", text, re.I) is not None

def extract_skills(text: str) -> list[str]:
    lower = text.lower()
    return sorted([skill for skill, aliases in SKILL_ALIASES.items() if any(_contains(lower, a) for a in aliases)])

def extract_email(text: str) -> str | None:
    m = re.search(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", text, re.I)
    return m.group(0) if m else None

def extract_phone(text: str) -> str | None:
    matches = re.findall(r"(?:\+91[-\s]?)?[6-9]\d{9}", text)
    return matches[0] if matches else None

def extract_name(text: str) -> str:
    for line in [x.strip() for x in text.splitlines() if x.strip()][:8]:
        if len(line.split()) in (2, 3) and not any(ch.isdigit() for ch in line) and "@" not in line:
            if not any(word.lower() in line.lower() for word in ["resume", "curriculum", "objective", "skills", "profile"]):
                return line[:200]
    return "Unknown Candidate"

def extract_years_experience(text: str) -> float:
    patterns = [r"(\d+(?:\.\d+)?)\s*\+?\s*years?\s*(?:of)?\s*(?:professional\s*)?experience",
                r"(\d+(?:\.\d+)?)\s*years?\s*experience"]
    for p in patterns:
        m = re.search(p, text, re.I)
        if m:
            return float(m.group(1))
    return 0.0

def extract_education(text: str) -> list[str]:
    lines = [x.strip() for x in text.splitlines() if x.strip()]
    terms = ["b.tech", "btech", "b.e", "bachelor", "m.tech", "mtech", "master", "mca", "bca", "mba", "computer science", "information technology"]
    return [line[:250] for line in lines if any(t in line.lower() for t in terms)][:8]

def extract_certifications(text: str) -> list[str]:
    lines = [x.strip() for x in text.splitlines() if x.strip()]
    return [line[:250] for line in lines if any(t in line.lower() for t in ["certification", "certified", "certificate", "aws certified", "ibm", "microsoft azure"])][:8]

def extract_projects(text: str) -> list[str]:
    lines = [x.strip() for x in text.splitlines() if x.strip()]
    return [line[:250] for line in lines if any(t in line.lower() for t in ["project", "developed", "built", "implemented"])][:10]

def parse_resume(text: str) -> dict:
    return {
        "name": extract_name(text),
        "email": extract_email(text),
        "phone": extract_phone(text),
        "skills": extract_skills(text),
        "experience_years": extract_years_experience(text),
        "education": extract_education(text),
        "certifications": extract_certifications(text),
        "projects": extract_projects(text),
    }
