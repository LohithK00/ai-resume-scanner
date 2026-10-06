from pathlib import Path
import fitz
from docx import Document

ALLOWED = {".pdf", ".docx"}

def extract_text(path: str) -> str:
    ext = Path(path).suffix.lower()
    if ext not in ALLOWED:
        raise ValueError("Only PDF and DOCX files are supported")
    if ext == ".pdf":
        doc = fitz.open(path)
        return "\n".join(page.get_text() for page in doc).strip()
    doc = Document(path)
    return "\n".join(p.text for p in doc.paragraphs).strip()
