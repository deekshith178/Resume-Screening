# development.md — Full Implementation Document

This is the **complete**, expanded, production-ready development plan for implementing the **Resume Shortlisting & Candidate Guidance System**. It integrates:
- NLP intake pipeline
- Synonym normalization engine
- ML scoring & clustering
- Hybrid candidate detection
- Recruiter dashboard & overrides
- Candidate portal & test-fit
- Guidance module (kNN)
- Security, deployment, APIs, and architecture

All content below is consolidated from our full discussion.

---
# 1. Executive Summary
This project is an intelligent hiring system that automatically shortlists resumes using NLP + ML while also assisting unselected candidates with personalized guidance. Recruiters keep full control through overrides and adjustable scoring weights. The system further includes:
- Resume ingestion (PDF/DOCX/TXT)
- NLP text extraction & sectioning
- Synonym normalization (skills mapping)
- SBERT embeddings + structured features
- Clustering into profession zones
- Weighted scoring engine
- Hybrid profile detection
- Candidate portal
- Agentic notifications
- Security (HMAC, JWT, scanning)

This document details EXACTLY how to build the whole system end-to-end.

---
# 2. High-Level Architecture
```
Candidate/Recruiter UI
    ↓ HTTPS
Backend API (FastAPI / Warp)
    - Auth (JWT/HMAC)
    - Shortlisting engine
    - Guidance engine
    - Notification orchestrator
    - Upload handler

Worker Queue (Celery / Redis)
    - File parsing
    - Embeddings
    - NLP pipeline
    - Clustering updates

ML Service (Python SBERT)
    - Embeddings
    - Canonical skill matching

Storage:
- PostgreSQL (+ pgvector)
- MinIO/S3 for resumes
- Redis for tasks
- ClamAV for scanning
```

---
# 3. Data Model
**candidates:** id, token_hash, email_encrypted, resume_path, vector, score, status, hybrid_flag, roles

**jobs:** id, title, jd_vector, centroid, created_at

**scores:** candidate_id, job_id, score, components_json

**audit_logs:** action, recruiter_id, timestamp, metadata

**guidance_history:** candidate_id, missing_skills

---
# 4. NLP Intake Pipeline
This is the pipeline responsible for converting ANY resume into machine-understandable text + structured features.

### 4.1 Steps
1. File uploaded → presigned MinIO URL
2. Virus scan (ClamAV)
3. Parse file:
   - PDF → pdfminer/pymupdf
   - Scanned → OCR
   - DOCX → python-docx
4. Clean text:
   - lowercase
   - remove symbols
   - fix spacing
   - clean bullets
5. Section extraction using regex:
   - Skills
   - Experience
   - Education
   - Projects
   - Certifications
6. Skill extraction from Skills/Experience sections
7. Synonym normalization (Section 5)
8. Experience calculation by date parsing
9. Projects count: bullets under Projects
10. Cert count: Certifications section
11. Education ordinal mapping
12. SBERT embedding of cleaned text
13. Create **candidate NLP token**

---
# 5. Synonym Normalization Engine
Ensures similar/variant words become **canonical skills**.

### 5.1 Multi-layer Normalization
**Layer 1: Rule-based**
```
{"js": "javascript", "py": "python", "ml": "machine learning"}
```

**Layer 2: Fuzzy matching (typos)**
```
fuzz.ratio(word, skill) ≥ 85
```

**Layer 3: SBERT embedding similarity**
```
sim = cosine(E(word), E(canonical_skill))
if sim ≥ 0.75: normalize
```

### 5.2 Canonical Vocabulary
- Programming languages
- ML tools
- Cloud tech
- Frameworks
- Databases

### 5.3 Output
A clean list like:
```
['python', 'machine learning', 'react', 'sql']
```

---
# 6. Feature Engineering & Fusion
### Numeric features:
- Experience (years)
- Projects
- Certificates
- Education level

Normalize with MinMaxScaler:
```
x' = (x - min) / (max - min)
```

### Final vector:
```
final_vec = [SBERT_vector || experience_norm || projects_norm || certs_norm || edu_norm]
```

---
# 7. Embeddings & Clustering
### 7.1 Embeddings
Model: `all-MiniLM-L6-v2`
Output: 384/768-dim

### 7.2 Clustering
**K-Means** → known categories
**HDBSCAN** → auto detect new categories

### 7.3 Profession Centroid
Mean of vectors in a cluster.

---
# 8. Scoring Model
### Variables:
- `S` = skill similarity (cosine scoring)
- `E` = experience norm
- `P` = project norm
- `C` = cert norm

### Formula:
\[
Score = 100(w_S S + w_E E + w_P P + w_C C)
\]

Default weights:
- wS = 0.50
- wE = 0.25
- wP = 0.15
- wC = 0.10

### Learned weights
Train Logistic Regression on `Selected` column.
Then normalize `coef_`.

---
# 9. Hybrid Candidate Detection
### Steps:
1. Compute similarity to ALL centroids
2. Sort top two
3. Compute:
\[
Confidence = sim_1 - sim_2
\]
4. If Confidence < 0.1 → **Hybrid**
5. Hybrid centroid:
\[
centroid_h = (centroid_1 + centroid_2)/2
\]
6. Recompute score with hybrid centroid

---
# 10. Guidance Engine (k-NN)
### Steps:
1. k-NN (k=5) on successful candidates
2. Compare skills → missing skills
3. Generate guidance list
4. Optional: call APIs
   - Coursera
   - Udemy
   - YouTube
5. Store results in guidance history

---
# 11. Candidate Portal
### Features:
- Login with HMAC token
- See application status
- See score breakdown
- Test-fit: paste JD → SBERT embedding → score
- Re-upload resume
- Get guidance

---
# 12. Recruiter Dashboard
### Features:
- Upload resumes
- Paste JD or choose job
- View ranked list
- Adjust weights (sliders)
- Override selection
- Publish results (agentic suggestion)
- See hybrid indicators
- Audit logs

---
# 13. Agentic Notification System
### Role:
- Prepare notifications
- Suggest publish timings
- Auto-draft emails
- Learn recruiter preferences (override data)

### Notifications sent to ALL:
- Selected
- Not selected

Recruiter decides WHEN.

---
# 14. Security
### Candidate Tokens
- Generate secure random token
- Store HMAC(token)
- Validate via HMAC compare

### Recruiter Auth
- JWT with roles

### Upload Security
- ClamAV scan
- MIME validation
- Size validation

### PII Protection
- Encrypt email/name fields
- Retention policy

### Logging
- Audit logs for overrides & publish

---
# 15. API Endpoints
### Upload
`POST /upload-url`
`POST /process-resume`

### Shortlisting
`POST /jobs`
`GET /jobs/{id}/shortlist`
`POST /jobs/{id}/override`
`POST /jobs/{id}/publish`

### Candidate
`POST /candidate/login`
`GET /candidate/{id}/status`
`POST /candidate/{id}/test-fit`
`POST /candidate/{id}/optin-guidance`
`GET /candidate/{id}/guidance-preview`

---
# 16. Deployment (Local → Cloud)
### Local
- Docker Compose: Postgres, MinIO, Redis, ClamAV, ML service, Backend

### Cloud
- S3, RDS, ElastiCache
- Load balancer + HTTPS
- Secrets Manager

---
# 17. Testing
- Unit: parser, embedding
- Integration: resume → score
- Security: token validation, upload scan
- E2E: recruiter workflow

---
# 18. Repo Structure
```
project/
├─ backend/
├─ ml_service/
├─ worker/
├─ frontend/
├─ data/
├─ docs/
└─ docker-compose.yml
```

---
# 19. MVP Checklist
- Resume parsing → SBERT → score
- Recruiter shortlist UI
- Candidate portal
- k-NN guidance
- Hybrid detection

---
# 20. Full Feature Checklist
(ALL modules from this document implemented)

