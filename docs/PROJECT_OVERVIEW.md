# Project Overview

## Title
AI-Powered Resume Screening and Candidate Shortlisting System Using Natural Language Processing

## Problem
Recruiters may receive a large number of resumes for one position. Manual screening is slow and inconsistent. A job-relevant automated screening assistant can reduce repetitive work by extracting information and ranking candidates against a job description.

## Proposed System
The application accepts a job description and PDF/DOCX resumes. It extracts text, identifies job-relevant skills and profile information, computes skill overlap and text similarity, scores experience/education/certifications, and produces an explainable candidate ranking.

## Architecture

```text
Recruiter
   |
   v
React Dashboard
   |
   v
FastAPI REST API
   |
   +------------------+
   |                  |
   v                  v
Document Parser     Job Analyzer
   |                  |
   v                  v
NLP/Profile -------- Matching Engine
                       |
                       v
                 Scoring Engine
                       |
                       v
                 PostgreSQL/SQLite
                       |
                       v
                 Ranking + Reports
```

## Modules

1. Job Profile Management
2. Resume Upload and Validation
3. Document Text Extraction
4. NLP/Profile Extraction
5. Job Description Analysis
6. Candidate Matching
7. Explainable Scoring
8. Candidate Ranking
9. Recruiter Analytics
10. Report Export

## AI methodology

The prototype uses a deterministic NLP pipeline and TF-IDF cosine similarity. This is intentional for reproducibility in a college environment. A later production version can replace the similarity component with a sentence-transformer embedding model while retaining the same scoring interface.

## Ethical considerations

Only job-relevant information should influence scoring. Sensitive attributes such as religion, caste, political affiliation, health information and similar protected/sensitive data must not be used for ranking. The system should assist human review rather than automatically determine employment outcomes.
