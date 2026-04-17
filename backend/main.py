from __future__ import annotations

from pathlib import Path
from typing import Optional, Dict, List, Tuple, Union
import sys
import logging

# Add parent directory to Python path to find modules in project root
sys.path.insert(0, str(Path(__file__).parent.parent))

import json
import os
import requests

# Set up logging
logger = logging.getLogger(__name__)
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, status, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

from score_resume_file import train_pipeline as train_file_pipeline, score_resume_file, load_trained_pipeline
from score_new_resumes import train_pipeline as train_text_pipeline, score_single_resume
from guidance_engine import GuidanceEngine, CORE_SKILLS_BY_CATEGORY
from nlp.nlp_intake import NLPIntakePipeline, CandidateToken
from backend.database import Base, engine, get_session
from backend.models import Candidate, Job, GuidanceOptIn, GuidanceRecommendation, CandidateScore, AuditLog, Recruiter
from backend.storage_service import get_storage_service
from backend.email_service import get_email_service
from backend.security import (
    create_recruiter_access_token,
    generate_candidate_token,
    get_current_recruiter,
    hash_token,
    get_password_hash,
    verify_token,
    verify_recruiter_credentials,
)


app = FastAPI(title="Resume Shortlisting & Guidance API", version="0.1.0")

# File upload validation constants
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_MIME_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",  # .docx
    "application/msword",  # .doc (legacy)
    "text/plain",  # .txt
}
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".doc", ".txt"}

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://localhost:3002", "http://localhost:3003", "http://localhost:3004", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root endpoint for better DX
@app.get("/")
async def root():
    return {
        "message": "Backend is running!",
        "docs": "http://localhost:8000/docs",
        "frontend": "http://localhost:3000"
    }

# SERP API key for guidance engine (loaded from .env file)
SERPAPI_KEY = os.getenv("SERPAPI_KEY")


# Global (in-memory) ML pipeline state for demo purposes only.
_FILE_PIPELINE = None
_FILE_CATEGORIES: list[str] | None = None
_TEXT_PIPELINE = None
_TEXT_CATEGORIES: list[str] | None = None
_TRAINING_DF = None  # Training dataset for k-NN guidance


@app.on_event("startup")
async def startup_event():
    """Initialize the backend on startup."""
    global _FILE_PIPELINE, _FILE_CATEGORIES, _TRAINING_DF
    
    # 1. Initialize Database
    print("[startup] Initializing database...")
    Base.metadata.create_all(bind=engine)
    
    # 2. Seed Demo Data (Recruiters)
    from backend.create_admin import create_admin
    create_admin()
    
    # 3. Load Training Dataset (for k-NN guidance)
    print("[startup] Loading training dataset...")
    unified_path = Path("unified_resume_dataset.csv")
    if unified_path.exists():
        try:
            import pandas as pd
            _TRAINING_DF = pd.read_csv(str(unified_path))
            print(f"[startup] Training dataset loaded: {len(_TRAINING_DF)} rows")
        except Exception as e:
            print(f"[startup] Failed to load training dataset: {e}")
            _TRAINING_DF = None
    else:
        print("[startup] Training dataset not found. k-NN guidance will use fallback method.")
        _TRAINING_DF = None
    
    # 4. Load ML Pipeline
    print("[startup] Loading ML pipeline...")
    model_path = Path("trained_pipeline.joblib")
    
    if model_path.exists():
        try:
            print(f"[startup] Found existing model at {model_path}, loading...")
            _FILE_PIPELINE, _FILE_CATEGORIES = load_trained_pipeline(str(model_path))
            print(f"[startup] Model loaded successfully. Categories: {_FILE_CATEGORIES}")
        except Exception as e:
            print(f"[startup] Failed to load model: {e}")
            _FILE_PIPELINE = None
            _FILE_CATEGORIES = None
    else:
        print("[startup] Model not found. Training new model (this may take a minute)...")
        try:
            _FILE_PIPELINE, _FILE_CATEGORIES = train_file_pipeline()
            # Save it for next time
            import joblib
            joblib.dump((_FILE_PIPELINE, _FILE_CATEGORIES), str(model_path))
            print("[startup] Training complete and model saved.")
        except Exception as e:
            print(f"[startup] Training failed: {e}")
            print("[startup] WARNING: Running without ML pipeline. Resume scoring will return dummy data.")


# --- Guidance resource aggregation (SerpAPI or static) --------------------------------

SERPAPI_API_KEY = os.environ.get("SERPAPI_API_KEY")


class ResourceAggregator:
    """Aggregate recommended learning resources per skill.

    Uses SerpAPI if configured; otherwise falls back to static course/video URLs.
    """

    def __init__(self) -> None:
        self.api_key = SERPAPI_API_KEY

    def _fallback_links(self, skill: str) -> List[str]:
        skill_slug = skill.replace(" ", "+")
        return [
            f"https://www.coursera.org/search?query={skill_slug}",
            f"https://www.udemy.com/courses/search/?q={skill_slug}",
            f"https://www.youtube.com/results?search_query={skill_slug}+tutorial",
        ]

    def search(
        self,
        skill: str,
        level: str | None = None,
        free_only: bool = False,
        limit: int = 5,
    ) -> List[Dict]:
        query = f"learn {skill}"
        if level:
            query += f" {level}"
        if free_only:
            query += " free"

        # No key configured -> simple static links
        if not self.api_key:
            return [
                {"title": f"Learn {skill}", "url": u, "source": "static"}
                for u in self._fallback_links(skill)[:limit]
            ]

        try:
            params = {
                "engine": "google",
                "q": query,
                "api_key": self.api_key,
                "num": limit,
            }
            resp = requests.get("https://serpapi.com/search", params=params, timeout=8)
            resp.raise_for_status()
            data = resp.json()
        except Exception:
            # Resilient fallback if external API fails
            return [
                {"title": f"Learn {skill}", "url": u, "source": "static"}
                for u in self._fallback_links(skill)[:limit]
            ]

        results: List[Dict] = []
        for item in data.get("organic_results", []):
            link = item.get("link")
            title = item.get("title")
            if not link:
                continue
            results.append(
                {
                    "title": title or f"Learn {skill}",
                    "url": link,
                    "source": "serpapi",
                }
            )
            if len(results) >= limit:
                break

        if not results:
            return [
                {"title": f"Learn {skill}", "url": u, "source": "static"}
                for u in self._fallback_links(skill)[:limit]
            ]
        return results


# --- Request / Response Models --------------------------------------------------------

class FileShortlistRequest(BaseModel):
    resume_path: str
    weights_path: Optional[str] = None


class FileShortlistResponse(BaseModel):
    path: str
    best_category: str
    best_index: int
    score: float
    normalized_similarity_best: float
    E_norm: float
    P_norm: float
    C_norm: float
    is_hybrid: bool
    confidence_gap: float
    skills: list[str]
    summary: str


class TextTestFitRequest(BaseModel):
    resume_text: str
    years_experience: float
    projects_count: float
    certificates_count: float
    weights_path: Optional[str] = None


class JobDescriptionTestFitRequest(BaseModel):
    candidate_id: str
    token: str
    job_description: str


class JobDescriptionTestFitResponse(BaseModel):
    score: float
    match_percentage: float
    best_category: str
    components: Dict[str, float]
    message: str


class TextTestFitResponse(BaseModel):
    best_category: str
    best_index: int
    score: float
    normalized_similarity_best: float
    E_norm: float
    P_norm: float
    C_norm: float
    is_hybrid: bool
    confidence_gap: float


class GuidanceRequest(BaseModel):
    resume_path: str
    category: str


class GuidanceResponse(BaseModel):
    category: str
    missing_skills: list[str]
    suggested_resources: dict[str, list[dict[str, str]]]


class RecruiterLoginRequest(BaseModel):
    username: str
    password: str


class RecruiterLoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str = "recruiter"


class RegisterRecruiterRequest(BaseModel):
    email: str
    password: str
    name: Optional[str] = None


class RegisterRecruiterResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    email: str
    name: Optional[str] = None
    role: str


class CandidateLoginRequest(BaseModel):
    candidate_id: str
    token: str


class CandidateStatusResponse(BaseModel):
    candidate_id: str
    name: str | None = None
    email: str | None = None
    status: str
    score: float | None = None
    category: str | None = None
    skills: List[str] | None = None
    components: Dict[str, float] | None = None


class CandidateGuidanceRequest(BaseModel):
    candidate_id: str
    token: str
    category: Optional[str] = None


class CandidateTokenRequest(BaseModel):
    email: str


class CandidateTokenResponse(BaseModel):
    message: str
    token: Optional[str] = None
    candidate_id: Optional[str] = None


# --- Job Management Models ---------------------------------------------------------


class CreateJobRequest(BaseModel):
    id: str
    title: str
    category: str
    required_skills: Optional[str] = None
    min_years_experience: float = 0.0
    description: Optional[str] = None


class JobResponse(BaseModel):
    id: str
    title: str
    category: str
    required_skills: Optional[str] = None
    min_years_experience: float
    description: Optional[str] = None
    created_at: str
    candidate_count: int = 0


class ShortlistCandidateItem(BaseModel):
    candidate_id: str
    name: str
    email: str
    score: float
    is_selected: bool
    is_override: bool
    category: str
    skills: Optional[str] = None
    components: Optional[Dict[str, float]] = None


class ShortlistResponse(BaseModel):
    job_id: str
    job_title: str
    candidates: List[ShortlistCandidateItem]
    total_count: int
    selected_count: int


class JobListResponse(BaseModel):
    items: List[JobResponse]
    total: int
    limit: int
    offset: int


class OverrideRequest(BaseModel):
    candidate_id: str
    is_selected: bool


class OverrideResponse(BaseModel):
    job_id: str
    candidate_id: str
    is_selected: bool
    is_override: bool
    message: str


class PublishRequest(BaseModel):
    notify_candidates: bool = True


class PublishResponse(BaseModel):
    job_id: str
    published: bool
    candidates_notified: int
    message: str


# --- Upload Models ------------------------------------------------------------------


class UploadUrlRequest(BaseModel):
    filename: str
    content_type: Optional[str] = None


class UploadUrlResponse(BaseModel):
    upload_url: str
    file_path: str
    expires_in: int = 3600  # seconds


class ProcessResumeRequest(BaseModel):
    file_path: str
    candidate_id: Optional[str] = None
    email: Optional[str] = None
    name: Optional[str] = None


class ProcessResumeResponse(BaseModel):
    candidate_id: str
    resume_path: str
    category: str
    score: Optional[float] = None
    skills: List[str]
    summary: str


# --- Startup -------------------------------------------------------------------------


@app.on_event("startup")
async def startup_event() -> None:
    """Initialize database schema and train initial ML pipelines.

    For production, model training would be offline and models loaded from disk.
    """
    global _FILE_PIPELINE, _FILE_CATEGORIES, _TEXT_PIPELINE, _TEXT_CATEGORIES

    # Ensure DB schema exists
    Base.metadata.create_all(bind=engine)

    # Seed one demo candidate + job if they do not exist yet
    from sqlalchemy import select

    with get_session() as db:
        # Note: Admin user is created by create_admin() function above
        # This section is kept for backward compatibility but create_admin() takes precedence

        if not db.execute(select(Candidate).where(Candidate.id == "cand_xyz")).scalar_one_or_none():
            # Generate a demo candidate login token and log it for local testing.
            demo_token = generate_candidate_token()
            candidate = Candidate(
                id="cand_xyz",
                email="demo.candidate@example.com",
                name="Demo Candidate",
                resume_path="tests/data/sample_resume.txt",
                category="Data Science",
            )
            db.add(candidate)
            # Print to stdout so you can copy for portal testing.
            print(f"[startup] Demo candidate 'cand_xyz' token (keep secret): {demo_token}")
        if not db.execute(select(Job).where(Job.id == "oracle-ds-1")).scalar_one_or_none():
            db.add(
                Job(
                    id="oracle-ds-1",
                    title="Data Scientist",
                    category="Data Science",
                    description="Data Scientist role focusing on Python, NumPy and SciPy.",
                    required_skills="numpy,scipy",
                    min_years_experience=2.0,
                )
            )

    # Train ML pipelines (with error handling for missing dependencies)
    try:
        print("[startup] Training ML pipelines...")
        _FILE_PIPELINE, _FILE_CATEGORIES = train_file_pipeline()
        _TEXT_PIPELINE, _TEXT_CATEGORIES = train_text_pipeline()
        print("[startup] ML pipelines trained successfully")
    except Exception as e:
        print(f"[startup] WARNING: ML pipeline training failed: {e}")
        print("[startup] Backend will start but ML features may be limited")
        print("[startup] Install missing packages: pip install pandas numpy scikit-learn sentence-transformers")
        _FILE_PIPELINE = None
        _FILE_CATEGORIES = None
        _TEXT_PIPELINE = None
        _TEXT_CATEGORIES = None


# --- Health --------------------------------------------------------------------------


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


# --- Auth: Recruiter login ------------------------------------------------------------


@app.post("/auth/recruiter/login", response_model=RecruiterLoginResponse)
async def recruiter_login(req: RecruiterLoginRequest) -> RecruiterLoginResponse:
    """Simple demo recruiter login that returns a JWT access token.

    In production this should verify against a real user store.
    """
    import logging
    from sqlalchemy import select
    
    logger = logging.getLogger("uvicorn")
    logger.info(f"[LOGIN] Attempting login for username: {req.username}")
    
    # ⚠️ TEMPORARY DEV BYPASS - REMOVE IN PRODUCTION ⚠️
    if req.username == "test@example.com" and req.password == "password123":
        logger.info(f"[LOGIN] DEV BYPASS - Allowing test account")
        # Still lookup the user to get their recruiter_id for proper job filtering
        with get_session() as db:
            dev_user = db.execute(select(Recruiter).where(Recruiter.email == req.username)).scalars().first()
            dev_user_id = dev_user.id if dev_user else None
        token = create_recruiter_access_token(subject=req.username, role="admin", recruiter_id=dev_user_id)
        return RecruiterLoginResponse(access_token=token, role="admin")
    # ⚠️ END DEV BYPASS ⚠️
    
    # Verify credentials
    creds_valid = verify_recruiter_credentials(req.username, req.password)
    logger.info(f"[LOGIN] Credentials valid: {creds_valid}")
    
    if not creds_valid:
        logger.warning(f"[LOGIN] FAILED - Invalid credentials for {req.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid recruiter credentials",
        )

    
    # Fetch user role from database
    with get_session() as db:
        user = db.execute(select(Recruiter).where(Recruiter.email == req.username)).scalars().first()
        if not user:
            logger.warning(f"[LOGIN] FAILED - User not found in database: {req.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid recruiter credentials",
            )
        user_role = user.role
        user_id = user.id
        logger.info(f"[LOGIN] User role: {user_role}, ID: {user_id}")

    token = create_recruiter_access_token(subject=req.username, role=user_role, recruiter_id=user_id)
    logger.info(f"[LOGIN] SUCCESS - Token created for {req.username} with role {user_role}")
    return RecruiterLoginResponse(access_token=token, role=user_role)


@app.post("/auth/recruiter/register", response_model=RegisterRecruiterResponse)
async def register_recruiter(req: RegisterRecruiterRequest) -> RegisterRecruiterResponse:
    """Register a new recruiter and return an access token."""
    from sqlalchemy import select
    import logging
    
    logger = logging.getLogger("uvicorn")
    logger.info(f"[REGISTER] Attempting registration for: {req.email}")

    with get_session() as db:
        # Check if email exists
        existing = db.execute(select(Recruiter).where(Recruiter.email == req.email)).scalars().first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )
        
        # Create new recruiter
        new_recruiter = Recruiter(
            email=req.email,
            name=req.name,
            hashed_password=get_password_hash(req.password),
            role="recruiter",
        )
        db.add(new_recruiter)
        db.commit()
        db.refresh(new_recruiter)
        
        # Create access token (auto-login)
        token = create_recruiter_access_token(subject=new_recruiter.email, role=new_recruiter.role, recruiter_id=new_recruiter.id)
        
        return RegisterRecruiterResponse(
            access_token=token,
            email=new_recruiter.email,
            name=new_recruiter.name,
            role=new_recruiter.role
        )


class CandidateRequestTokenRequest(BaseModel):
    email: str


@app.post("/auth/candidate/request-token")
async def request_candidate_token(req: CandidateRequestTokenRequest):
    """Demo endpoint: Get candidate token by email. 
    In production, this would send an email. Here it returns the token directly.
    """
    from sqlalchemy import select
    
    with get_session() as db:
        candidate = db.execute(select(Candidate).where(Candidate.email == req.email)).scalars().first()
        if not candidate:
            raise HTTPException(status_code=404, detail="Candidate email not found")
        
        # In a real app, we would verify the token hash or generate a new one
        # For this demo, we can't easily reverse the hash, so we might need to regenerate it
        # OR, since we stored the token_hash, we can't return the raw token!
        # This is a security feature.
        
        # For the DEMO to work with the frontend 'alice' flow, let's just generate a NEW token and save it.
        new_token = generate_candidate_token()
        candidate.token_hash = hash_token(new_token)
        db.commit()
        
        return {
            "success": True,
            "message": "Login link generated",
            "token": new_token,
            "candidate_id": candidate.id
        }



# --- Recruiter Profile Endpoints ---------------------------------------------------


class RecruiterProfileResponse(BaseModel):
    id: int
    email: str
    name: Optional[str] = None
    role: str
    jobs_count: int = 0
    candidates_count: int = 0


class UpdateRecruiterProfileRequest(BaseModel):
    name: Optional[str] = None
    current_password: Optional[str] = None
    new_password: Optional[str] = None


@app.get("/recruiters/me", response_model=RecruiterProfileResponse)
async def get_recruiter_profile(
    recruiter: dict = Depends(get_current_recruiter),
) -> RecruiterProfileResponse:
    """Get current recruiter's profile with stats."""
    from sqlalchemy import select, func

    recruiter_id = recruiter.get("recruiter_id")
    if not recruiter_id:
        raise HTTPException(status_code=401, detail="Invalid token - no recruiter ID")

    with get_session() as db:
        rec = db.execute(select(Recruiter).where(Recruiter.id == recruiter_id)).scalars().first()
        if not rec:
            raise HTTPException(status_code=404, detail="Recruiter not found")

        # Count jobs and candidates
        jobs_count = db.execute(
            select(func.count()).select_from(Job).where(Job.recruiter_id == recruiter_id)
        ).scalar() or 0

        candidates_count = db.execute(
            select(func.count()).select_from(Candidate).where(Candidate.recruiter_id == recruiter_id)
        ).scalar() or 0

        return RecruiterProfileResponse(
            id=rec.id,
            email=rec.email,
            name=rec.name,
            role=rec.role,
            jobs_count=jobs_count,
            candidates_count=candidates_count,
        )


@app.put("/recruiters/me", response_model=RecruiterProfileResponse)
async def update_recruiter_profile(
    req: UpdateRecruiterProfileRequest,
    recruiter: dict = Depends(get_current_recruiter),
) -> RecruiterProfileResponse:
    """Update current recruiter's profile (name and/or password)."""
    from sqlalchemy import select, func

    recruiter_id = recruiter.get("recruiter_id")
    if not recruiter_id:
        raise HTTPException(status_code=401, detail="Invalid token - no recruiter ID")

    with get_session() as db:
        rec = db.execute(select(Recruiter).where(Recruiter.id == recruiter_id)).scalars().first()
        if not rec:
            raise HTTPException(status_code=404, detail="Recruiter not found")

        # Update name if provided
        if req.name is not None:
            rec.name = req.name

        # Update password if both current and new provided
        if req.current_password and req.new_password:
            from backend.security import verify_password
            if not verify_password(req.current_password, rec.hashed_password):
                raise HTTPException(status_code=400, detail="Current password is incorrect")
            rec.hashed_password = get_password_hash(req.new_password)

        db.commit()
        db.refresh(rec)

        # Get updated counts
        jobs_count = db.execute(
            select(func.count()).select_from(Job).where(Job.recruiter_id == recruiter_id)
        ).scalar() or 0

        candidates_count = db.execute(
            select(func.count()).select_from(Candidate).where(Candidate.recruiter_id == recruiter_id)
        ).scalar() or 0

        return RecruiterProfileResponse(
            id=rec.id,
            email=rec.email,
            name=rec.name,
            role=rec.role,
            jobs_count=jobs_count,
            candidates_count=candidates_count,
        )


# --- Recruiter-style endpoint: file-based shortlist ----------------------------------


@app.post("/jobs/test-shortlist", response_model=FileShortlistResponse)
async def test_shortlist(
    req: FileShortlistRequest,
    _: dict = Depends(get_current_recruiter),
) -> FileShortlistResponse:
    """Run end-to-end scoring for a single resume file.

    This uses the same logic as score_resume_file.py, wired via the global
    trained pipeline.
    """
    if _FILE_PIPELINE is None or _FILE_CATEGORIES is None:
        raise HTTPException(status_code=500, detail="ML pipeline not initialized")

    weights_path = req.weights_path
    w_S = w_E = w_P = w_C = None
    if weights_path is not None:
        weights_file = Path(weights_path)
        if not weights_file.exists():
            raise HTTPException(status_code=400, detail=f"Weights file not found: {weights_path}")
        import json

        with weights_file.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if "weights" in data:
            weights = data["weights"]
        else:
            weights = data
        w_S = float(weights.get("w_S")) if "w_S" in weights else None
        w_E = float(weights.get("w_E")) if "w_E" in weights else None
        w_P = float(weights.get("w_P")) if "w_P" in weights else None
        w_C = float(weights.get("w_C")) if "w_C" in weights else None

    result = score_resume_file(
        _FILE_PIPELINE,
        _FILE_CATEGORIES,
        req.resume_path,
        w_S=w_S,
        w_E=w_E,
        w_P=w_P,
        w_C=w_C,
    )

    return FileShortlistResponse(**result)


# --- Candidate-style endpoint: text test-fit -----------------------------------------


@app.post("/candidate/test-fit", response_model=TextTestFitResponse)
async def candidate_test_fit(req: TextTestFitRequest) -> TextTestFitResponse:
    """Test-fit a candidate's resume text against the existing profession centroids.

    This uses the same scoring function as score_new_resumes.py.
    """
    if _TEXT_PIPELINE is None or _TEXT_CATEGORIES is None:
        raise HTTPException(status_code=500, detail="ML pipeline not initialized")

    weights_path = req.weights_path
    w_S = w_E = w_P = w_C = None
    if weights_path is not None:
        weights_file = Path(weights_path)
        if not weights_file.exists():
            raise HTTPException(status_code=400, detail=f"Weights file not found: {weights_path}")
        import json

        with weights_file.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if "weights" in data:
            weights = data["weights"]
        else:
            weights = data
        w_S = float(weights.get("w_S")) if "w_S" in weights else None
        w_E = float(weights.get("w_E")) if "w_E" in weights else None
        w_P = float(weights.get("w_P")) if "w_P" in weights else None
        w_C = float(weights.get("w_C")) if "w_C" in weights else None

    result = score_single_resume(
        _TEXT_PIPELINE,
        resume_text=req.resume_text,
        years_experience=req.years_experience,
        projects_count=req.projects_count,
        certificates_count=req.certificates_count,
        w_S=w_S,
        w_E=w_E,
        w_P=w_P,
        w_C=w_C,
    )

    best_idx = result["best_profession_index"]
    best_category = _TEXT_CATEGORIES[best_idx] if 0 <= best_idx < len(_TEXT_CATEGORIES) else "(unknown)"

    return TextTestFitResponse(
        best_category=best_category,
        best_index=best_idx,
        score=result["score"],
        normalized_similarity_best=max(result["normalized_similarity"]),
        E_norm=result["E_norm"],
        P_norm=result["P_norm"],
        C_norm=result["C_norm"],
        is_hybrid=result["is_hybrid"],
        confidence_gap=result["confidence_gap"],
    )


@app.post("/candidate/test-fit-job", response_model=JobDescriptionTestFitResponse)
async def candidate_test_fit_job(req: JobDescriptionTestFitRequest) -> JobDescriptionTestFitResponse:
    """Test-fit a candidate's stored resume against a job description.
    
    This endpoint:
    1. Gets the candidate's resume from the database
    2. Extracts resume data using NLP
    3. Compares job description against resume using embeddings
    4. Returns a match score
    """
    from sqlalchemy import select as sa_select
    import numpy as np
    from sklearn.metrics.pairwise import cosine_similarity
    
    # 1. Validate auth
    if req.token == "demo-token-bypass" and req.candidate_id == "cand_xyz":
        pass  # Skip verification
    else:
        with get_session() as db:
            cand = db.execute(sa_select(Candidate).where(Candidate.id == req.candidate_id)).scalars().first()
            if not cand or not cand.token_hash:
                raise HTTPException(status_code=404, detail="Candidate not found")
            if not verify_token(req.token, cand.token_hash):
                raise HTTPException(status_code=401, detail="Invalid token")
    
    # 2. Get candidate's resume
    with get_session() as db:
        cand = db.execute(sa_select(Candidate).where(Candidate.id == req.candidate_id)).scalars().first()
        if not cand or not cand.resume_path:
            raise HTTPException(status_code=404, detail="Resume not found for candidate")
        resume_path = cand.resume_path
    
    # 3. Get file path for processing (handles Azure URLs)
    storage_service = get_storage_service()
    try:
        processing_path = storage_service.get_file_path(resume_path)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=f"Resume file not found: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error accessing resume file: {str(e)}")
    
    # 4. Track temp file for cleanup
    temp_file_to_delete = None
    if storage_service.use_azure and processing_path != resume_path:
        try:
            import tempfile
            if processing_path.startswith(tempfile.gettempdir()):
                temp_file_to_delete = processing_path
        except:
            pass
    
    # 5. Extract resume data using NLP
    nlp_pipeline = NLPIntakePipeline()
    try:
        token: CandidateToken = nlp_pipeline.build_candidate_token(processing_path)
    except Exception as e:
        # Clean up temp file on error
        if temp_file_to_delete:
            try:
                os.unlink(temp_file_to_delete)
            except:
                pass
        raise HTTPException(status_code=500, detail=f"Error processing resume: {str(e)}")
    
    # 6. Score resume using ML pipeline
    if _FILE_PIPELINE is None or _FILE_CATEGORIES is None:
        raise HTTPException(status_code=500, detail="ML pipeline not initialized")
    
    # Build candidate's feature vector
    semantic_vec = token.embedding.reshape(1, -1)
    structured_vec = _FILE_PIPELINE.transform_structured_row(
        years_experience=token.experience,
        projects_count=token.projects,
        certificates_count=token.certifications,
    )
    candidate_vec = _FILE_PIPELINE.fuse_features(semantic_vec, structured_vec)[0]
    
    # 7. Compare job description against candidate's resume
    # Encode job description
    jd_vec = _FILE_PIPELINE.embedder.encode([req.job_description])[0]
    
    # Calculate similarity between JD and candidate resume
    similarity = cosine_similarity(jd_vec.reshape(1, -1), candidate_vec.reshape(1, -1))[0][0]
    similarity_normalized = (similarity + 1) / 2.0  # Normalize to 0-1
    
    # Also get profession match
    sims, sims_norm = _FILE_PIPELINE.skill_similarity(candidate_vec.reshape(1, -1))
    best_idx = int(np.argmax(sims_norm))
    best_category = _FILE_CATEGORIES[best_idx] if 0 <= best_idx < len(_FILE_CATEGORIES) else "General"
    
    # Calculate overall score (weighted combination)
    E_norm, P_norm, C_norm = structured_vec[0]
    S = float(sims_norm[best_idx])
    
    # Use JD similarity as the main factor, but also consider profession match
    # Blend: 70% JD similarity, 30% profession match
    blended_similarity = 0.7 * similarity_normalized + 0.3 * S
    
    # Calculate final score using the scoring formula
    score = _FILE_PIPELINE.compute_scores(
        S=blended_similarity,
        E=E_norm,
        P=P_norm,
        C=C_norm,
    )
    
    match_percentage = float(similarity_normalized * 100)
    
    # Clean up temp file if it was downloaded from Azure (after successful processing)
    if temp_file_to_delete:
        try:
            os.unlink(temp_file_to_delete)
        except:
            pass
    
    # Generate message
    if match_percentage >= 80:
        message = "Excellent match! Your skills and experience align well with this position."
    elif match_percentage >= 60:
        message = "Good potential match. Consider highlighting relevant experience."
    else:
        message = "Consider upskilling in areas mentioned in the job description."
    
    return JobDescriptionTestFitResponse(
        score=score,
        match_percentage=match_percentage,
        best_category=best_category,
        components={
            "job_description_similarity": float(similarity_normalized),
            "profession_match": float(S),
            "experience": float(E_norm),
            "projects": float(P_norm),
            "certifications": float(C_norm),
        },
        message=message,
    )


# --- Candidate-style endpoint: guidance for a file -----------------------------------


@app.post("/candidate/guidance/request", response_model=GuidanceResponse)
async def candidate_guidance_request(req: CandidateGuidanceRequest) -> GuidanceResponse:
    """Run guidance for a specific candidate ID, using their stored resume."""
    from sqlalchemy import select as sa_select

    # 1. Validate auth
    # --- DEV BYPASS ---
    if req.token == "demo-token-bypass" and req.candidate_id == "cand_xyz":
        pass # Skip verification
    else:
        with get_session() as db:
            cand = db.execute(sa_select(Candidate).where(Candidate.id == req.candidate_id)).scalars().first()
            if not cand or not cand.token_hash:
                raise HTTPException(status_code=404, detail="Candidate not found")
            if not verify_token(req.token, cand.token_hash):
                raise HTTPException(status_code=401, detail="Invalid token")

    # 2. Get candidate resume path
    resume_path = None
    category = req.category or "General"
    
    with get_session() as db:
        cand = db.execute(sa_select(Candidate).where(Candidate.id == req.candidate_id)).scalars().first()
        if cand:
             resume_path = cand.resume_path
             if not req.category:
                 category = cand.category or "General"
    
    if not resume_path:
        raise HTTPException(status_code=404, detail="Resume not found for candidate")

    # 3. Get file path for processing (handles Azure URLs)
    storage_service = get_storage_service()
    
    # Check if it's a test file path (fallback for demo)
    if resume_path == "tests/data/sample_resume.txt":
        if os.path.exists("backend/tests/data/sample_resume.txt"):
            resume_path = "backend/tests/data/sample_resume.txt"
    
    # Get processing path (downloads from Azure if needed)
    try:
        processing_path = storage_service.get_file_path(resume_path)
    except FileNotFoundError:
        raise HTTPException(status_code=400, detail=f"Resume file missing at {resume_path}")

    # 4. Run Guidance
    nlp_pipeline = NLPIntakePipeline()
    # Note: build_candidate_token might re-parse file. 
    # Optimization: store extracted skills in DB to avoid re-parsing.
    # For now, we re-parse.
    
    token: CandidateToken = nlp_pipeline.build_candidate_token(processing_path)
    
    # Clean up temp file if it was downloaded from Azure
    if storage_service.use_azure and processing_path != resume_path:
        try:
            import tempfile
            if processing_path.startswith(tempfile.gettempdir()):
                os.unlink(processing_path)
        except:
            pass
    # Use name/email from DB if token extraction missed them? 
    # The pipeline extracts from text, usually good.

    # Initialize guidance engine with ML pipeline if available
    ge = GuidanceEngine(
        serpapi_key=SERPAPI_KEY,
        ml_pipeline=_FILE_PIPELINE,
        training_df=_TRAINING_DF,
    )
    g_res = ge.generate_guidance(token, category, top_n=10, use_kmeans=True)

    return GuidanceResponse(
        category=category,
        missing_skills=g_res.missing_skills,
        suggested_resources=g_res.suggested_resources,
    )


@app.post("/candidate/guidance", response_model=GuidanceResponse)
async def candidate_guidance(req: GuidanceRequest) -> GuidanceResponse:
    """Run NLP intake on a resume file and return missing core skills + resources."""
    nlp_pipeline = NLPIntakePipeline()
    token: CandidateToken = nlp_pipeline.build_candidate_token(req.resume_path)

    # Initialize guidance engine with ML pipeline if available
    ge = GuidanceEngine(
        serpapi_key=SERPAPI_KEY,
        ml_pipeline=_FILE_PIPELINE,
        training_df=_TRAINING_DF,
    )
    g_res = ge.generate_guidance(token, req.category, top_n=10, use_kmeans=True)

    return GuidanceResponse(
        category=req.category,
        missing_skills=g_res.missing_skills,
        suggested_resources=g_res.suggested_resources,
    )


# --- Candidate auth & status ----------------------------------------------------------


@app.post("/auth/candidate/request-token", response_model=CandidateTokenResponse)
async def request_candidate_token(req: CandidateTokenRequest) -> CandidateTokenResponse:
    """Request a login token for a candidate email (Simulated Magic Link)."""
    from sqlalchemy import select as sa_select

    # --- DEV BYPASS ---
    if req.email == "demo.candidate@example.com":
        return CandidateTokenResponse(
            message="Login link generated (DEMO BYPASS)",
            token="demo-token-bypass",
            candidate_id="cand_xyz"
        )
    # ------------------

    with get_session() as db:
        cand = db.execute(sa_select(Candidate).where(Candidate.email == req.email)).scalars().first()
        if not cand:
            raise HTTPException(status_code=404, detail="Email not found. Please upload a resume first.")

        raw_token = generate_candidate_token()
        cand.token_hash = hash_token(raw_token)
        db.add(cand)
        db.commit()

        return CandidateTokenResponse(
            message="Login link generated",
            token=raw_token,
            candidate_id=cand.id
        )


@app.post("/candidate/login", response_model=CandidateStatusResponse)
async def candidate_login(req: CandidateLoginRequest) -> CandidateStatusResponse:
    """Candidate login using opaque HMAC token."""
    from sqlalchemy import select as sa_select

    # --- DEV BYPASS ---
    if req.token == "demo-token-bypass":
        # Force login for demo candidate
        with get_session() as db:
            # Ensure cand_xyz exists or pick valid one
            cand = db.execute(sa_select(Candidate).where(Candidate.id == "cand_xyz")).scalars().first()
            if not cand:
                # Fallback: pick first candidate if cand_xyz missing
                cand = db.execute(sa_select(Candidate)).scalars().first()
            
            if not cand:
                 raise HTTPException(status_code=404, detail="No candidates in DB to bypass with.")

            # Derive status for bypass
            score_record = db.execute(sa_select(CandidateScore).where(CandidateScore.candidate_id == cand.id)).scalars().first()
            
            status = "new"
            score = None
            if score_record:
                score = score_record.score
                status = "shortlisted" if (score_record.is_selected or score_record.is_override) else "scored"

            # Parse skills from JSON string if available
            skills = None
            if cand.skills:
                try:
                    skills = json.loads(cand.skills) if isinstance(cand.skills, str) else cand.skills
                except:
                    skills = None

            # Parse components from JSON string if available
            components = None
            if score_record and score_record.components_json:
                try:
                    components = json.loads(score_record.components_json) if isinstance(score_record.components_json, str) else score_record.components_json
                except:
                    components = None

            return CandidateStatusResponse(
                candidate_id=cand.id,
                name=cand.name,
                email=cand.email,
                status=status,
                score=score,
                category=cand.category,
                skills=skills,
                components=components,
            )
    # ------------------

    with get_session() as db:
        cand = (
            db.execute(sa_select(Candidate).where(Candidate.id == req.candidate_id))
            .scalars()
            .first()
        )
        if not cand or not cand.token_hash:
            raise HTTPException(status_code=404, detail="Candidate not found")

        if not verify_token(req.token, cand.token_hash):
            raise HTTPException(status_code=401, detail="Invalid candidate token")

        # Derive status/score from CandidateScore (same as candidate_status)
        score_record = db.execute(sa_select(CandidateScore).where(CandidateScore.candidate_id == cand.id)).scalars().first()

        status = "new"
        score = None
        if score_record:
            score = score_record.score
            if score_record.is_selected:
                 status = "shortlisted"
            elif score_record.is_override:
                 status = "shortlisted"
            else:
                 status = "scored"

        # Parse skills from JSON string if available
        skills = None
        if cand.skills:
            try:
                skills = json.loads(cand.skills) if isinstance(cand.skills, str) else cand.skills
            except:
                skills = None

        # Parse components from JSON string if available
        components = None
        if score_record and score_record.components_json:
            try:
                components = json.loads(score_record.components_json) if isinstance(score_record.components_json, str) else score_record.components_json
            except:
                components = None

        return CandidateStatusResponse(
            candidate_id=cand.id,
            name=cand.name,
            email=cand.email,
            status=status,
            score=score,
            category=cand.category,
            skills=skills,
            components=components,
        )


@app.get("/candidate/{candidate_id}/status", response_model=CandidateStatusResponse)
async def candidate_status(candidate_id: str, token: str) -> CandidateStatusResponse:
    """Return candidate status for portal, validating the same HMAC token."""
    from sqlalchemy import select as sa_select

    # --- DEV BYPASS ---
    if token == "demo-token-bypass":
         with get_session() as db:
            cand = db.execute(sa_select(Candidate).where(Candidate.id == candidate_id)).scalars().first()
            if not cand:
                 raise HTTPException(status_code=404, detail="Candidate not found")
            
            score_record = db.execute(sa_select(CandidateScore).where(CandidateScore.candidate_id == candidate_id)).scalars().first()

            status = "new"
            score = None
            if score_record:
                score = score_record.score
                if score_record.is_selected:
                        status = "shortlisted"
                elif score_record.is_override:
                        status = "shortlisted"
                else:
                        status = "scored"

            # Parse skills from JSON string if available
            skills = None
            if cand.skills:
                try:
                    import json
                    skills = json.loads(cand.skills) if isinstance(cand.skills, str) else cand.skills
                except:
                    skills = None

            # Parse components from JSON string if available
            components = None
            if score_record and score_record.components_json:
                try:
                    components = json.loads(score_record.components_json) if isinstance(score_record.components_json, str) else score_record.components_json
                except:
                    components = None

            return CandidateStatusResponse(
                candidate_id=cand.id,
                name=cand.name,
                email=cand.email,
                status=status,
                score=score,
                category=cand.category,
                skills=skills,
                components=components,
            )
    # ------------------

    with get_session() as db:
        cand = (
            db.execute(sa_select(Candidate).where(Candidate.id == candidate_id))
            .scalars()
            .first()
        )
        if not cand or not cand.token_hash:
            raise HTTPException(status_code=404, detail="Candidate not found")

        if not verify_token(token, cand.token_hash):
            raise HTTPException(status_code=401, detail="Invalid candidate token")

        # Look up the latest application/score for this candidate (demo logic: just pick the first one or default)
        score_record = db.execute(sa_select(CandidateScore).where(CandidateScore.candidate_id == candidate_id)).scalars().first()

        status = "new"
        score = None
        if score_record:
            score = score_record.score
            if score_record.is_selected:
                 status = "shortlisted"
            elif score_record.is_override:
                 status = "shortlisted" # Approximating override as shortlisted
            else:
                 status = "scored"

        # Parse skills from JSON string if available
        skills = None
        if cand.skills:
            try:
                import json
                skills = json.loads(cand.skills) if isinstance(cand.skills, str) else cand.skills
            except:
                skills = None

        # Parse components from JSON string if available
        components = None
        if score_record and score_record.components_json:
            try:
                components = json.loads(score_record.components_json) if isinstance(score_record.components_json, str) else score_record.components_json
            except:
                components = None

        return CandidateStatusResponse(
            candidate_id=cand.id,
            name=cand.name,
            email=cand.email,
            status=status,
            score=score,
            category=cand.category,
            skills=skills,
            components=components,
        )


# --- Generate Candidate Portal Link (for recruiters) ---------------------------------


class CandidatePortalLinkResponse(BaseModel):
    candidate_id: str
    portal_url: str
    token: str
    message: str


@app.post("/candidates/{candidate_id}/portal-link", response_model=CandidatePortalLinkResponse)
async def generate_portal_link(
    candidate_id: str,
    recruiter: dict = Depends(get_current_recruiter),
) -> CandidatePortalLinkResponse:
    """Generate a portal access link for a candidate.
    
    This endpoint is for recruiters to generate shareable links that candidates
    can use to access their portal with their status and guidance information.
    """
    from sqlalchemy import select as sa_select

    with get_session() as db:
        cand = db.execute(sa_select(Candidate).where(Candidate.id == candidate_id)).scalars().first()
        if not cand:
            raise HTTPException(status_code=404, detail="Candidate not found")

        # Generate a new token for this candidate
        new_token = generate_candidate_token()
        cand.token_hash = hash_token(new_token)
        db.commit()

        # Build the portal URL
        # The frontend base URL - in production this would come from config
        frontend_base_url = os.environ.get("FRONTEND_URL", "http://localhost:3000")
        portal_url = f"{frontend_base_url}/candidate/portal?candidate_id={candidate_id}&token={new_token}"

        return CandidatePortalLinkResponse(
            candidate_id=candidate_id,
            portal_url=portal_url,
            token=new_token,
            message=f"Portal link generated for {cand.name or cand.email}"
        )


# --- Candidate guidance opt-in, preview, and send (mock implementation) ---------------


# Opt-in + cached previews: keys are (candidate_id, job_id)
GUIDANCE_OPTINS: set[Tuple[str, str]] = set()
GUIDANCE_CACHE: Dict[Tuple[str, str], Dict] = {}


def get_candidate_by_id(candidate_id: str) -> Dict[str, str] | None:
    """Fetch a candidate and return a simple dict, detached from the DB session."""
    from sqlalchemy import select

    with get_session() as db:
        row = (
            db.execute(select(Candidate).where(Candidate.id == candidate_id))
            .scalars()
            .first()
        )
        if row is None:
            return None
        return {
            "id": row.id,
            "email": row.email,
            "name": row.name,
            "resume_path": row.resume_path,
            "category": row.category,
        }


def get_job_by_id(job_id: str) -> Dict[str, str] | None:
    """Fetch a job and return a simple dict, detached from the DB session."""
    from sqlalchemy import select

    with get_session() as db:
        row = db.execute(select(Job).where(Job.id == job_id)).scalars().first()
        if row is None:
            return None
        return {
            "id": row.id,
            "title": row.title,
            "category": row.category,
            "required_skills": row.required_skills or "",
            "min_years_experience": str(row.min_years_experience),
        }


class OptInRequest(BaseModel):
    job_id: str


class OptInResponse(BaseModel):
    candidate_id: str
    job_id: str
    status: str


@app.post("/candidates/{candidate_id}/optin-guidance", response_model=OptInResponse)
async def optin_guidance(candidate_id: str, req: OptInRequest) -> OptInResponse:
    cand = get_candidate_by_id(candidate_id)
    job = get_job_by_id(req.job_id)
    if not cand:
        raise HTTPException(status_code=404, detail="Candidate not found")
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    key = (candidate_id, req.job_id)
    GUIDANCE_OPTINS.add(key)

    # Persist opt-in record
    with get_session() as db:
        db.add(GuidanceOptIn(candidate_id=candidate_id, job_id=req.job_id))

    return OptInResponse(candidate_id=candidate_id, job_id=req.job_id, status="opted_in")


class GuidancePreview(BaseModel):
    candidate_id: str
    job_id: str
    missing_skills: List[str]
    resources: Dict[str, List[Dict]]


@app.get("/candidates/{candidate_id}/guidance-preview", response_model=GuidancePreview)
async def guidance_preview(candidate_id: str, job_id: str) -> GuidancePreview:
    key = (candidate_id, job_id)
    if key not in GUIDANCE_OPTINS:
        raise HTTPException(status_code=403, detail="Candidate has not opted in for guidance")

    cand = get_candidate_by_id(candidate_id)
    job = get_job_by_id(job_id)
    if not cand or not job:
        raise HTTPException(status_code=404, detail="Candidate or job not found")

    # Access resume_path from detached candidate dict
    resume_path = cand["resume_path"]

    # Get file path for processing (handles Azure URLs)
    storage_service = get_storage_service()
    try:
        processing_path = storage_service.get_file_path(resume_path)
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail=f"Resume file not found: {resume_path}")

    nlp_pipeline = NLPIntakePipeline()
    try:
        token: CandidateToken = nlp_pipeline.build_candidate_token(processing_path)
        
        # Clean up temp file if it was downloaded from Azure
        if storage_service.use_azure and processing_path != resume_path:
            try:
                import tempfile
                if processing_path.startswith(tempfile.gettempdir()):
                    os.unlink(processing_path)
            except:
                pass
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail=f"Resume file not found: {resume_path}")

    # Initialize guidance engine with ML pipeline if available
    ge = GuidanceEngine(
        serpapi_key=SERPAPI_KEY,
        ml_pipeline=_FILE_PIPELINE,
        training_df=_TRAINING_DF,
    )
    category = job["category"]
    # required_skills stored as comma-separated string
    extra_skills = [s.strip() for s in (job["required_skills"] or "").split(",") if s.strip()]
    base_core = CORE_SKILLS_BY_CATEGORY.get(category, [])
    merged_core = sorted({s.lower() for s in base_core + extra_skills})
    ge.core_skills_by_category[category] = merged_core

    missing, _, method = ge.compute_missing_skills(token, category, top_n=10, use_kmeans=True)

    agg = ResourceAggregator()
    resources: Dict[str, List[Dict]] = {}
    for skill in missing:
        resources[skill] = agg.search(skill, limit=5)

    preview_dict = {
        "candidate_id": candidate_id,
        "job_id": job_id,
        "missing_skills": missing,
        "resources": resources,
    }
    GUIDANCE_CACHE[key] = preview_dict

    # Persist recommendation snapshot (JSON-serialized)
    with get_session() as db:
        db.add(
            GuidanceRecommendation(
                candidate_id=candidate_id,
                job_id=job_id,
                missing_skills_json=json.dumps(missing),
                resources_json=json.dumps(resources),
                delivered=False,
                delivery_channel=None,
            )
        )

    return GuidancePreview(**preview_dict)


class SendGuidanceRequest(BaseModel):
    channel: str = "email"  # "email" or "dashboard"


class SendGuidanceResponse(BaseModel):
    candidate_id: str
    job_id: str
    channel: str
    status: str


@app.post("/candidates/{candidate_id}/send-guidance", response_model=SendGuidanceResponse)
async def send_guidance(candidate_id: str, job_id: str, req: SendGuidanceRequest) -> SendGuidanceResponse:
    key = (candidate_id, job_id)
    preview = GUIDANCE_CACHE.get(key)
    if not preview:
        raise HTTPException(status_code=404, detail="No guidance preview found; call /guidance-preview first")

    cand = get_candidate_by_id(candidate_id)
    if not cand:
        raise HTTPException(status_code=404, detail="Candidate not found")

    email_service = get_email_service()
    
    if req.channel == "email":
        # Send guidance email
        try:
            # Get guidance data from cache
            guidance_data = {
                "resources": preview.get("resources", []),
                "missing_skills": preview.get("missing_skills", []),
            }
            
            # Generate portal URL (you may need to adjust this based on your frontend setup)
            portal_url = None  # Could be: f"http://localhost:3000/candidate/portal?token=..."
            
            success = email_service.send_guidance_email(
                candidate_email=cand.email,
                candidate_name=cand.name,
                guidance_data=guidance_data,
                portal_url=portal_url,
            )
            
            if success:
                status = "sent_email"
            else:
                status = "email_failed"  # Email service disabled or failed
        except Exception as e:
            logger.error(f"Failed to send guidance email to {cand.email}: {e}")
            status = "email_failed"
    else:
        status = "saved_to_dashboard"

    # Mark latest recommendation for this candidate/job as delivered
    from sqlalchemy import select

    with get_session() as db:
        rec = (
            db.execute(
                select(GuidanceRecommendation)
                .where(
                    GuidanceRecommendation.candidate_id == candidate_id,
                    GuidanceRecommendation.job_id == job_id,
                )
                .order_by(GuidanceRecommendation.created_at.desc())
            )
            .scalars()
            .first()
        )
        if rec:
            rec.delivered = True
            rec.delivery_channel = req.channel

    return SendGuidanceResponse(
        candidate_id=candidate_id,
        job_id=job_id,
        channel=req.channel,
        status=status,
    )


# --- Job Management Endpoints --------------------------------------------------------


def _log_audit_action(
    action: str,
    recruiter_id: Optional[str] = None,
    job_id: Optional[str] = None,
    candidate_id: Optional[str] = None,
    metadata: Optional[Dict] = None,
) -> None:
    """Helper to log audit actions."""
    with get_session() as db:
        log = AuditLog(
            action=action,
            recruiter_id=recruiter_id,
            job_id=job_id,
            candidate_id=candidate_id,
            metadata_json=json.dumps(metadata) if metadata else None,
        )
        db.add(log)


@app.post("/jobs", response_model=JobResponse)
async def create_job(
    req: CreateJobRequest,
    recruiter: dict = Depends(get_current_recruiter),
) -> JobResponse:
    """Create a new job posting."""
    from sqlalchemy import select

    with get_session() as db:
        # Check if job already exists
        existing = db.execute(select(Job).where(Job.id == req.id)).scalars().first()
        if existing:
            raise HTTPException(status_code=400, detail=f"Job with id '{req.id}' already exists")

        job = Job(
            id=req.id,
            title=req.title,
            category=req.category,
            description=req.description,
            required_skills=req.required_skills,
            min_years_experience=req.min_years_experience,
            recruiter_id=recruiter.get("recruiter_id"),
        )
        db.add(job)

        _log_audit_action(
            action="create_job",
            recruiter_id=recruiter.get("sub"),
            job_id=req.id,
            metadata={"title": req.title, "category": req.category},
        )
        db.commit()
        db.refresh(job)

        response = JobResponse(
            id=job.id,
            title=job.title,
            category=job.category,
            required_skills=job.required_skills,
            min_years_experience=job.min_years_experience,
            description=job.description,
            created_at=job.created_at.isoformat(),
            candidate_count=0,
        )

    return response


@app.get("/jobs", response_model=JobListResponse)
async def list_jobs(
    recruiter: dict = Depends(get_current_recruiter),
    limit: int = 50,
    offset: int = 0,
) -> JobListResponse:
    """Return a paginated list of jobs."""
    from sqlalchemy import select, func, or_

    with get_session() as db:
        # Get recruiter_id from token
        recruiter_id = recruiter.get("recruiter_id")
        is_admin = recruiter.get("role") == "admin"
        
        # Filter jobs by recruiter if recruiter_id is set and not admin
        # Include jobs with recruiter_id = None (legacy/unassigned jobs) for all recruiters
        # Admin or no recruiter_id - see all jobs
        count_stmt = select(func.count()).select_from(Job)
        total = db.execute(count_stmt).scalar() or 0
        
        # Query all jobs with candidate count
        stmt = (
            select(Job, func.count(CandidateScore.id))
            .outerjoin(CandidateScore, Job.id == CandidateScore.job_id)
            .group_by(Job.id, Job.created_at)
            .order_by(Job.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        
        results = db.execute(stmt).all()

        # Build job_items INSIDE session context to avoid DetachedInstanceError
        job_items = []
        for job, count in results:
            job_items.append(
                JobResponse(
                    id=job.id,
                    title=job.title,
                    category=job.category,
                    required_skills=job.required_skills,
                    min_years_experience=job.min_years_experience,
                    description=job.description,
                    created_at=job.created_at.isoformat(),
                    candidate_count=count,
                )
            )

    return JobListResponse(items=job_items, total=total, limit=limit, offset=offset)


@app.delete("/jobs/{job_id}")
async def delete_job(
    job_id: str,
    recruiter: dict = Depends(get_current_recruiter),
) -> dict:
    """Delete a job posting."""
    from sqlalchemy import select

    with get_session() as db:
        job = db.execute(select(Job).where(Job.id == job_id)).scalars().first()
        if not job:
            raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")

        # Optional: Delete associated scores/recommendations if cascade not set
        # For now, we assume simple delete is sufficient or DB handles foreign keys
        db.delete(job)
        
        _log_audit_action(
            action="delete_job",
            recruiter_id=recruiter.get("sub"),
            job_id=job_id,
        )
        db.commit()

    return {"status": "deleted", "id": job_id}


@app.get("/jobs/{job_id}/shortlist", response_model=ShortlistResponse)
async def get_job_shortlist(
    job_id: str,
    recruiter: dict = Depends(get_current_recruiter),
    limit: int = 100,
    offset: int = 0,
    compute_scores: bool = True,
) -> ShortlistResponse:
    """Get shortlisted candidates for a job, ranked by score.
    
    If compute_scores=True and no scores exist, will compute scores for all candidates
    matching the job category.
    """
    from sqlalchemy import select, desc, func

    with get_session() as db:
        # Get job
        job = db.execute(select(Job).where(Job.id == job_id)).scalars().first()
        if not job:
            raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")

        # Check if scores exist, if not and compute_scores=True, compute them
        existing_scores_count = (
            db.execute(select(func.count()).select_from(CandidateScore).where(CandidateScore.job_id == job_id))
            .scalar()
        )

        # Get recruiter_id from token
        recruiter_id = recruiter.get("recruiter_id")
        is_admin = recruiter.get("role") == "admin"
        
        # Verify job belongs to this recruiter (if recruiter_id is set and not admin)
        # Allow access if:
        # 1. User is admin
        # 2. Job has no recruiter_id (legacy/unassigned jobs - accessible to all)
        # 3. Job belongs to this recruiter
        # UPDATE: We now allow ALL recruiters to access ALL jobs (Open Marketplace), 
        # but they will only see their own candidates (filtered below).
        # if recruiter_id is not None and not is_admin:
        #     if job.recruiter_id is not None and job.recruiter_id != recruiter_id:
        #         raise HTTPException(
        #             status_code=403, 
        #             detail=f"Job '{job_id}' does not belong to your account"
        #         )

        if existing_scores_count == 0 and compute_scores and _FILE_PIPELINE is not None:
            # Compute scores for candidates matching the job category AND recruiter (if recruiter_id is set and not admin)
            candidate_query = select(Candidate).where(Candidate.category == job.category)
            if recruiter_id is not None and recruiter.get("role") != "admin":
                # Only score candidates owned by this recruiter (non-admins)
                candidate_query = candidate_query.where(Candidate.recruiter_id == recruiter_id)
            
            candidates = db.execute(candidate_query).scalars().all()

            for candidate in candidates:
                try:
                    result = score_resume_file(
                        _FILE_PIPELINE,
                        _FILE_CATEGORIES,
                        candidate.resume_path,
                    )

                    score_obj = CandidateScore(
                        candidate_id=candidate.id,
                        job_id=job_id,
                        score=result["score"],
                        is_selected=False,
                        is_override=False,
                        components_json=json.dumps({
                            "normalized_similarity": result["normalized_similarity_best"],
                            "E_norm": result["E_norm"],
                            "P_norm": result["P_norm"],
                            "C_norm": result["C_norm"],
                        }),
                    )
                    db.add(score_obj)
                except Exception as e:
                    # Skip candidates with processing errors
                    print(f"Warning: Failed to score candidate {candidate.id}: {e}")
                    continue

            db.commit()

        # Get candidate scores for this job, filtered by recruiter ownership (unless admin)
        score_query = (
            select(CandidateScore, Candidate)
            .join(Candidate, CandidateScore.candidate_id == Candidate.id)
            .where(CandidateScore.job_id == job_id)
        )
        
        # Filter by recruiter_id if set and not admin
        if recruiter_id is not None and recruiter.get("role") != "admin":
            score_query = score_query.where(Candidate.recruiter_id == recruiter_id)
        
        scores = (
            db.execute(
                score_query
                .order_by(desc(CandidateScore.score))
                .limit(limit)
                .offset(offset)
            )
            .all()
        )

        candidate_items = []
        selected_count = 0

        for score_obj, candidate in scores:
            # Parse skills from JSON string if available
            skills_parsed = None
            if candidate.skills:
                try:
                    if isinstance(candidate.skills, str):
                        skills_parsed = json.loads(candidate.skills)
                    else:
                        skills_parsed = candidate.skills
                except:
                    # If parsing fails, try to treat as single skill string
                    skills_parsed = candidate.skills if isinstance(candidate.skills, list) else [candidate.skills] if candidate.skills else None
            
            candidate_items.append(
                ShortlistCandidateItem(
                    candidate_id=candidate.id,
                    name=candidate.name,
                    email=candidate.email,
                    score=score_obj.score,
                    is_selected=score_obj.is_selected,
                    is_override=score_obj.is_override,
                    category=candidate.category,
                    skills=json.dumps(skills_parsed) if skills_parsed else None,  # Keep as JSON string for consistency
                    components=json.loads(score_obj.components_json) if score_obj.components_json else {},
                )
            )
            if score_obj.is_selected:
                selected_count += 1

        # Get total count, filtered by recruiter if applicable (unless admin)
        if recruiter_id is not None and recruiter.get("role") != "admin":
            # Join with Candidate to filter by recruiter_id
            total_count = (
                db.execute(
                    select(func.count())
                    .select_from(CandidateScore)
                    .join(Candidate, CandidateScore.candidate_id == Candidate.id)
                    .where(
                        CandidateScore.job_id == job_id,
                        Candidate.recruiter_id == recruiter_id
                    )
                )
                .scalar() or 0
            )
        else:
            # Admin or no recruiter filter - count all candidates for this job
            total_count = (
                db.execute(select(func.count()).select_from(CandidateScore).where(CandidateScore.job_id == job_id))
                .scalar() or 0
            )

        response = ShortlistResponse(
            job_id=job_id,
            job_title=job.title,
            candidates=candidate_items,
            total_count=total_count,
            selected_count=selected_count,
        )

    return response


@app.post("/jobs/{job_id}/override", response_model=OverrideResponse)
async def override_candidate_selection(
    job_id: str,
    req: OverrideRequest,
    recruiter: dict = Depends(get_current_recruiter),
) -> OverrideResponse:
    """Override candidate selection status (manually select/deselect)."""
    from sqlalchemy import select

    with get_session() as db:
        # Verify job exists
        job = db.execute(select(Job).where(Job.id == job_id)).scalars().first()
        if not job:
            raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")

        # Get or create candidate score
        score = (
            db.execute(
                select(CandidateScore).where(
                    CandidateScore.job_id == job_id,
                    CandidateScore.candidate_id == req.candidate_id,
                )
            )
            .scalars()
            .first()
        )

        if not score:
            raise HTTPException(
                status_code=404,
                detail=f"Candidate '{req.candidate_id}' not found in shortlist for job '{job_id}'",
            )

        # Update selection status
        score.is_selected = req.is_selected
        score.is_override = True

        _log_audit_action(
            action="override",
            recruiter_id=recruiter.get("sub"),
            job_id=job_id,
            candidate_id=req.candidate_id,
            metadata={"is_selected": req.is_selected, "previous_selected": not req.is_selected},
        )

    return OverrideResponse(
        job_id=job_id,
        candidate_id=req.candidate_id,
        is_selected=req.is_selected,
        is_override=True,
        message=f"Candidate selection {'enabled' if req.is_selected else 'disabled'} via override",
    )


@app.post("/jobs/{job_id}/publish", response_model=PublishResponse)
async def publish_job_results(
    job_id: str,
    req: PublishRequest,
    recruiter: dict = Depends(get_current_recruiter),
) -> PublishResponse:
    """Publish shortlist results and optionally notify candidates."""
    from sqlalchemy import select

    with get_session() as db:
        # Verify job exists
        job = db.execute(select(Job).where(Job.id == job_id)).scalars().first()
        if not job:
            raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")

        # Get selected candidates
        selected_scores = (
            db.execute(
                select(CandidateScore, Candidate)
                .join(Candidate, CandidateScore.candidate_id == Candidate.id)
                .where(
                    CandidateScore.job_id == job_id,
                    CandidateScore.is_selected == True,
                )
            )
            .all()
        )

        candidates_notified = 0
        if req.notify_candidates:
            # Send emails to selected candidates
            email_service = get_email_service()
            for score, candidate in selected_scores:
                try:
                    success = email_service.send_selection_notification(
                        candidate_email=candidate.email,
                        candidate_name=candidate.name,
                        job_title=job.title,
                        company_name="Our Company",  # Could be from Job model or config
                    )
                    if success:
                        candidates_notified += 1
                except Exception as e:
                    logger.error(f"Failed to send notification email to {candidate.email}: {e}")

        _log_audit_action(
            action="publish",
            recruiter_id=recruiter.get("sub"),
            job_id=job_id,
            metadata={
                "candidates_notified": candidates_notified,
                "total_selected": len(selected_scores),
            },
        )

    return PublishResponse(
        job_id=job_id,
        published=True,
        candidates_notified=candidates_notified,
        message=f"Job results published. {candidates_notified} candidates notified." if req.notify_candidates else "Job results published.",
    )


# --- Audit Log Endpoints -------------------------------------------------------------

class AuditLogResponse(BaseModel):
    id: int
    action: str
    recruiter_id: Optional[str]
    job_id: Optional[str]
    candidate_id: Optional[str]
    candidate_name: Optional[str] = None
    metadata_json: Optional[str]
    timestamp: str

class AuditLogListResponse(BaseModel):
    items: List[AuditLogResponse]
    total: int
    limit: int
    offset: int

@app.get("/audit-logs", response_model=AuditLogListResponse)
async def get_audit_logs(
    recruiter: dict = Depends(get_current_recruiter),
    limit: int = 50,
    offset: int = 0,
    action: Optional[str] = None,
) -> AuditLogListResponse:
    """Get paginated audit logs."""
    from sqlalchemy import select, desc, func

    with get_session() as db:
        query = select(AuditLog)
        
        if action:
            query = query.where(AuditLog.action == action)
            
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total = db.execute(count_query).scalar() or 0
        
        # Get items with explicit join for candidate names if we want them
        # For simplicity, let's just fetch logs and optionally resolve names 
        # But a join is better. Let's do a join.
        stmt = (
            select(AuditLog, Candidate.name)
            .outerjoin(Candidate, AuditLog.candidate_id == Candidate.id)
            .order_by(desc(AuditLog.timestamp))
            .limit(limit)
            .offset(offset)
        )
        
        if action:
            stmt = stmt.where(AuditLog.action == action)
            
        results = db.execute(stmt).all()
        
        items = []
        for log, candidate_name in results:
            items.append(
                AuditLogResponse(
                    id=log.id,
                    action=log.action,
                    recruiter_id=log.recruiter_id,
                    job_id=log.job_id,
                    candidate_id=log.candidate_id,
                    candidate_name=candidate_name or "Unknown",
                    metadata_json=log.metadata_json,
                    timestamp=log.timestamp.isoformat(),
                )
            )
            
    return AuditLogListResponse(items=items, total=total, limit=limit, offset=offset)


# --- Upload Endpoints ----------------------------------------------------------------

from fastapi import File, UploadFile, Form
import shutil

@app.post("/upload-resume", response_model=ProcessResumeResponse)
async def upload_resume_endpoint(
    file: UploadFile = File(...),
    candidate_id: str = Form(...),
):
    """Handle real file upload from frontend. Uses Azure Blob Storage if configured, otherwise local storage."""
    # 1. Read file content
    file_content = await file.read()
    
    # 2. Upload to storage (Azure or local)
    storage_service = get_storage_service()
    storage_path = storage_service.upload_file(
        file_content=file_content,
        filename=file.filename or "resume.pdf",
        content_type=file.content_type
    )
    
    # 3. Get local path for processing (downloads from Azure if needed)
    processing_path = storage_service.get_file_path(storage_path)
    
    # 4. Process it (reuse existing logic from process_resume)
    # Logic copied/adapted from process_resume to allow direct calling
    from sqlalchemy import select
    
    # a. NLP Intake
    nlp_pipeline = NLPIntakePipeline()
    token = nlp_pipeline.build_candidate_token(processing_path)
    
    # b. Score against all file categories
    if _FILE_PIPELINE is None or _FILE_CATEGORIES is None:
         # Fallback if ML not ready
         best_category = "General"
         score = 0.0
         skills = ["python", "communication"] # dummy
         summary = "ML pipeline not loaded"
    else:
        # We need a scoring function. existing score_resume_file takes a path
        # Let's use the loaded pipeline directly
        res = score_resume_file(_FILE_PIPELINE, _FILE_CATEGORIES, processing_path)
        best_category = res["best_category"]
        score = res["score"]
        skills = res["skills"]
        summary = res["summary"]
    
    # Clean up temp file if it was downloaded from Azure
    if storage_service.use_azure and processing_path != storage_path:
        try:
            import os
            os.unlink(processing_path)
        except:
            pass

    # c. Update Candidate Record
    with get_session() as db:
        cand = db.execute(select(Candidate).where(Candidate.id == candidate_id)).scalars().first()
        if cand:
            cand.resume_path = storage_path  # Store Azure URL or local path
            cand.category = best_category
            # Update name and email from NLP extraction if available
            if token.name and token.name.strip() and token.name.lower() != "unknown":
                cand.name = token.name
            if token.email and token.email.strip():
                cand.email = token.email
            # Update skills from NLP extraction (more reliable than ML result)
            if token.skills and len(token.skills) > 0:
                cand.skills = json.dumps(token.skills)
            elif skills:  # Fallback to ML result
                cand.skills = json.dumps(skills)
            if summary:
                cand.summary = summary
            
            # Update score if we have a job context? For now just save generic category/score
            # Ideally we score against the SPECIFIC job the user is applying for.
            # But the portal is generic "status". 
            
            # Let's update the score for the demo job "oracle-ds-1" if it exists, to simulate "Application"
            # This makes the "Status" tab update with the new score!
            job_id = "oracle-ds-1" 
            existing_score = db.execute(select(CandidateScore).where(
                CandidateScore.candidate_id == candidate_id,
                CandidateScore.job_id == job_id
            )).scalars().first()
            
            if existing_score:
                existing_score.score = score
                existing_score.components_json = json.dumps({"skills": skills, "summary": summary})
            
            db.commit()

    return ProcessResumeResponse(
        candidate_id=candidate_id,
        resume_path=storage_path,  # Azure URL or local path
        category=best_category,
        score=score,
        skills=skills,
        summary=summary,
    )



@app.post("/upload-url", response_model=UploadUrlResponse)
async def generate_upload_url(
    req: UploadUrlRequest,
    recruiter: dict = Depends(get_current_recruiter),
) -> UploadUrlResponse:
    """Generate a presigned URL for file upload.
    
    For MVP, this returns a local file path. In production, this would generate
    a presigned S3/MinIO URL.
    """
    import uuid
    from pathlib import Path

    # Validate file extension
    file_ext = Path(req.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # For MVP: create a local uploads directory
    uploads_dir = Path("uploads")
    uploads_dir.mkdir(exist_ok=True)

    # Generate unique filename
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = uploads_dir / unique_filename

    # In production, this would generate a presigned URL for S3/MinIO
    # For now, return the local path where the file should be uploaded
    upload_url = f"/api/upload/{unique_filename}"  # This would be the actual upload endpoint

    return UploadUrlResponse(
        upload_url=str(file_path),  # In production: presigned URL
        file_path=str(file_path),
        expires_in=3600,
    )


@app.post("/process-resume", response_model=ProcessResumeResponse)
async def process_resume(
    req: ProcessResumeRequest,
    recruiter: dict = Depends(get_current_recruiter),
) -> ProcessResumeResponse:
    """Process an uploaded resume file and create/update candidate record.
    
    This endpoint:
    1. Runs NLP intake on the resume
    2. Scores the candidate against all job categories
    3. Creates or updates candidate record
    4. Optionally matches against existing jobs
    """
    from pathlib import Path
    from sqlalchemy import select
    import uuid

    resume_path = Path(req.file_path)
    if not resume_path.exists():
        raise HTTPException(status_code=404, detail=f"Resume file not found: {req.file_path}")
    
    # Validate file size
    file_size = resume_path.stat().st_size
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File size ({file_size / (1024*1024):.1f}MB) exceeds maximum allowed size of {MAX_FILE_SIZE / (1024*1024):.1f}MB"
        )
    
    # Validate file extension
    file_ext = resume_path.suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # Run NLP intake
    nlp_pipeline = NLPIntakePipeline()
    try:
        token: CandidateToken = nlp_pipeline.build_candidate_token(str(resume_path))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process resume: {str(e)}")

    # Score against all categories
    if _FILE_PIPELINE is None or _FILE_CATEGORIES is None:
        raise HTTPException(status_code=500, detail="ML pipeline not initialized")

    result = score_resume_file(
        _FILE_PIPELINE,
        _FILE_CATEGORIES,
        str(resume_path),
    )

    # Create or update candidate
    candidate_id = req.candidate_id or f"cand_{uuid.uuid4().hex[:8]}"
    
    # Get recruiter_id from token (for candidate isolation)
    recruiter_id = recruiter.get("recruiter_id")
    
    with get_session() as db:
        candidate = (
            db.execute(select(Candidate).where(Candidate.id == candidate_id))
            .scalars()
            .first()
        )

        if candidate:
            # Update existing candidate
            candidate.resume_path = str(resume_path)
            candidate.category = result["best_category"]
            candidate.skills = json.dumps(result["skills"])
            candidate.summary = result["summary"]
            # Update recruiter_id if not set (for isolation)
            if recruiter_id is not None and candidate.recruiter_id is None:
                candidate.recruiter_id = recruiter_id
        else:
            # Create new candidate
            if not req.email or not req.name:
                raise HTTPException(
                    status_code=400,
                    detail="email and name are required for new candidates",
                )
            
            candidate_token = generate_candidate_token()
            candidate = Candidate(
                id=candidate_id,
                email=req.email,
                name=req.name,
                resume_path=str(resume_path),
                category=result["best_category"],
                skills=json.dumps(result["skills"]),
                summary=result["summary"],
                token_hash=hash_token(candidate_token),
                recruiter_id=recruiter_id,  # Assign to recruiter for isolation
            )
            db.add(candidate)
            print(f"[process-resume] Created candidate '{candidate_id}' with token: {candidate_token}")

        # Get recruiter_id and check if admin
        recruiter_id = recruiter.get("recruiter_id")
        is_admin = recruiter.get("role") == "admin"
        
        # Optionally score against existing jobs owned by this recruiter (if recruiter_id is set and not admin)
        if recruiter_id is not None and not is_admin:
            jobs = db.execute(select(Job).where(Job.recruiter_id == recruiter_id)).scalars().all()
        else:
            # Admin or no recruiter_id - score against all jobs
            jobs = db.execute(select(Job)).scalars().all()
        
        for job in jobs:
            # Check if candidate matches job category
            if job.category == result["best_category"]:
                # Score candidate for this job
                existing_score = (
                    db.execute(
                        select(CandidateScore).where(
                            CandidateScore.candidate_id == candidate_id,
                            CandidateScore.job_id == job.id,
                        )
                    )
                    .scalars()
                    .first()
                )

                if not existing_score:
                    score_obj = CandidateScore(
                        candidate_id=candidate_id,
                        job_id=job.id,
                        score=result["score"],
                        is_selected=False,
                        is_override=False,
                        components_json=json.dumps({
                            "normalized_similarity": result["normalized_similarity_best"],
                            "E_norm": result["E_norm"],
                            "P_norm": result["P_norm"],
                            "C_norm": result["C_norm"],
                        }),
                    )
                    db.add(score_obj)

        _log_audit_action(
            action="process_resume",
            recruiter_id=recruiter.get("sub"),
            candidate_id=candidate_id,
            metadata={"category": result["best_category"], "score": result["score"]},
        )

    return ProcessResumeResponse(
        candidate_id=candidate_id,
        resume_path=str(resume_path),
        category=result["best_category"],
        score=result["score"],
        skills=result["skills"],
        summary=result["summary"],
    )


@app.post("/batch-process-resumes")
async def batch_process_resumes(
    files: List[UploadFile] = File(...),
    job_id: str = Form(...),
    weights: str = Form(None),
    recruiter: dict = Depends(get_current_recruiter),
):
    """
    Upload and process multiple resume files in batch.
    
    Args:
        files: List of resume files (PDF, DOCX, TXT)
        job_id: ID of the job to match candidates against
        recruiter: Current authenticated recruiter
    
    Returns:
        List of processed candidates with scores
    """
    from pathlib import Path
    import uuid
    import shutil
    from sqlalchemy import select
    
    # Validate job exists
    with get_session() as db:
        job = db.execute(select(Job).where(Job.id == job_id)).scalars().first()
        if not job:
            raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")
    
    storage_service = get_storage_service()
    results = []
    errors = []
    
    for file in files:
        try:
            # Read file content
            file_content = await file.read()
            
            # Validate file size
            if len(file_content) > MAX_FILE_SIZE:
                errors.append({
                    "filename": file.filename,
                    "error": f"File size exceeds maximum allowed size of {MAX_FILE_SIZE / (1024*1024):.1f}MB"
                })
                continue
            
            # Validate MIME type
            if file.content_type and file.content_type not in ALLOWED_MIME_TYPES:
                errors.append({
                    "filename": file.filename,
                    "error": f"File type not allowed. Allowed types: PDF, DOCX, DOC, TXT"
                })
                continue
            
            # Validate file extension
            if file.filename:
                file_ext = Path(file.filename).suffix.lower()
                if file_ext not in ALLOWED_EXTENSIONS:
                    errors.append({
                        "filename": file.filename,
                        "error": f"File extension not allowed. Allowed extensions: {', '.join(ALLOWED_EXTENSIONS)}"
                    })
                    continue
            
            # Upload to storage (Azure or local)
            storage_path = storage_service.upload_file(
                file_content=file_content,
                filename=file.filename or "resume.pdf",
                content_type=file.content_type
            )
            
            # Get local path for processing (downloads from Azure if needed)
            processing_path = storage_service.get_file_path(storage_path)
            
            # Run NLP intake
            nlp_pipeline = NLPIntakePipeline()
            token: CandidateToken = nlp_pipeline.build_candidate_token(processing_path)
            
            # Score against all categories
            if _FILE_PIPELINE is None or _FILE_CATEGORIES is None:
                raise HTTPException(status_code=500, detail="ML pipeline not initialized")
            
            # Parse weights if provided
            w_S = w_E = w_P = w_C = None
            if weights:
                try:
                    weight_dict = json.loads(weights)
                    w_S = float(weight_dict.get("w_S", 50)) / 100.0
                    w_E = float(weight_dict.get("w_E", 25)) / 100.0
                    w_P = float(weight_dict.get("w_P", 15)) / 100.0
                    w_C = float(weight_dict.get("w_C", 10)) / 100.0
                except (json.JSONDecodeError, ValueError):
                    pass
            
            result = score_resume_file(
                _FILE_PIPELINE,
                _FILE_CATEGORIES,
                processing_path,
                w_S=w_S,
                w_E=w_E,
                w_P=w_P,
                w_C=w_C,
            )
            
            # Clean up temp file if it was downloaded from Azure
            if storage_service.use_azure and processing_path != storage_path:
                try:
                    import os
                    os.unlink(processing_path)
                except:
                    pass
            
            # Create candidate
            candidate_id = f"cand_{uuid.uuid4().hex[:8]}"
            
            with get_session() as db:
                candidate = Candidate(
                    id=candidate_id,
                    name=token.name or "Unknown",
                    email=token.email or f"{candidate_id}@placeholder.com",
                    resume_path=storage_path,  # Store Azure URL or local path
                    category=result["best_category"],
                    skills=json.dumps(result["skills"]),
                    summary=result["summary"],
                    recruiter_id=recruiter.get("recruiter_id"),
                )
                db.add(candidate)
                db.commit()
                
                # Create score record for this job
                score_record = CandidateScore(
                    candidate_id=candidate_id,
                    job_id=job_id,
                    score=result["score"],
                    components_json=json.dumps(result.get("breakdown", {})),
                )
                db.add(score_record)
                db.commit()
            
            results.append({
                "filename": file.filename,
                "candidate_id": candidate_id,
                "name": token.name,
                "email": token.email,
                "score": result["score"],
                "category": result["best_category"],
                "status": "success"
            })
            
            # Log audit action
            _log_audit_action(
                action="process_resume",
                recruiter_id=recruiter.get("sub"),
                job_id=job_id,
                candidate_id=candidate_id,
                metadata={"filename": file.filename, "score": result["score"]}
            )
            
        except Exception as e:
            errors.append({
                "filename": file.filename,
                "error": str(e),
                "status": "error"
            })
    
    return {
        "success": len(results),
        "failed": len(errors),
        "results": results,
        "errors": errors,
        "job_id": job_id
    }


# --- Admin Endpoints ------------------------------------------------------------

class AdminRecruiterResponse(BaseModel):
    id: int
    email: str
    name: Optional[str] = None
    role: str
    jobs_count: int = 0
    candidates_count: int = 0
    created_at: str

class AdminRecruiterListResponse(BaseModel):
    recruiters: List[AdminRecruiterResponse]
    total: int

class AdminCandidateResponse(BaseModel):
    id: str
    name: str
    email: str
    category: str
    recruiter_id: Optional[int] = None
    recruiter_email: Optional[str] = None
    skills: Optional[List[str]] = None
    created_at: str

class AdminCandidateListResponse(BaseModel):
    candidates: List[AdminCandidateResponse]
    total: int

class AdminUpdateRecruiterRequest(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    password: Optional[str] = None

class AdminUpdateCandidateRequest(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    category: Optional[str] = None
    recruiter_id: Optional[int] = None

def require_admin(recruiter: dict = Depends(get_current_recruiter)) -> dict:
    """Dependency to require admin role. Admin is separate from regular recruiters."""
    recruiter_role = recruiter.get("role")
    if recruiter_role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Admin access required. Only users with 'admin' role can access this endpoint."
        )
    return recruiter

@app.get("/admin/recruiters", response_model=AdminRecruiterListResponse)
async def admin_list_recruiters(
    recruiter: dict = Depends(require_admin),
    limit: int = 100,
    offset: int = 0,
) -> AdminRecruiterListResponse:
    """List all recruiters (admin only)."""
    from sqlalchemy import select, func
    
    with get_session() as db:
        # Get total count
        total = db.execute(select(func.count()).select_from(Recruiter)).scalar() or 0
        
        # Get recruiters with job and candidate counts
        recruiters = db.execute(
            select(Recruiter)
            .order_by(Recruiter.created_at.desc())
            .limit(limit)
            .offset(offset)
        ).scalars().all()
        
        recruiter_items = []
        for rec in recruiters:
            jobs_count = db.execute(
                select(func.count()).select_from(Job).where(Job.recruiter_id == rec.id)
            ).scalar() or 0
            
            candidates_count = db.execute(
                select(func.count()).select_from(Candidate).where(Candidate.recruiter_id == rec.id)
            ).scalar() or 0
            
            recruiter_items.append(
                AdminRecruiterResponse(
                    id=rec.id,
                    email=rec.email,
                    name=rec.name,
                    role=rec.role,
                    jobs_count=jobs_count,
                    candidates_count=candidates_count,
                    created_at=rec.created_at.isoformat(),
                )
            )
    
    return AdminRecruiterListResponse(recruiters=recruiter_items, total=total)

@app.get("/admin/candidates", response_model=AdminCandidateListResponse)
async def admin_list_candidates(
    recruiter: dict = Depends(require_admin),
    limit: int = 100,
    offset: int = 0,
    recruiter_id: Optional[int] = None,
) -> AdminCandidateListResponse:
    """List all candidates (admin only)."""
    from sqlalchemy import select, func
    
    with get_session() as db:
        # Build query with optional recruiter filter
        candidate_query = select(Candidate)
        if recruiter_id is not None:
            candidate_query = candidate_query.where(Candidate.recruiter_id == recruiter_id)
        
        # Get total count
        total = db.execute(select(func.count()).select_from(candidate_query.subquery())).scalar() or 0
        
        # Get candidates
        candidates = db.execute(
            candidate_query
            .order_by(Candidate.created_at.desc())
            .limit(limit)
            .offset(offset)
        ).scalars().all()
        
        candidate_items = []
        for cand in candidates:
            # Parse skills
            skills = None
            if cand.skills:
                try:
                    skills = json.loads(cand.skills) if isinstance(cand.skills, str) else cand.skills
                except:
                    skills = None
            
            # Get recruiter email if recruiter_id is set
            recruiter_email = None
            if cand.recruiter_id:
                rec = db.execute(select(Recruiter).where(Recruiter.id == cand.recruiter_id)).scalars().first()
                recruiter_email = rec.email if rec else None
            
            candidate_items.append(
                AdminCandidateResponse(
                    id=cand.id,
                    name=cand.name,
                    email=cand.email,
                    category=cand.category,
                    recruiter_id=cand.recruiter_id,
                    recruiter_email=recruiter_email,
                    skills=skills,
                    created_at=cand.created_at.isoformat(),
                )
            )
    
    return AdminCandidateListResponse(candidates=candidate_items, total=total)

@app.put("/admin/recruiters/{recruiter_id}", response_model=AdminRecruiterResponse)
async def admin_update_recruiter(
    recruiter_id: int,
    req: AdminUpdateRecruiterRequest,
    recruiter: dict = Depends(require_admin),
) -> AdminRecruiterResponse:
    """Update a recruiter (admin only)."""
    from sqlalchemy import select, func
    
    with get_session() as db:
        rec = db.execute(select(Recruiter).where(Recruiter.id == recruiter_id)).scalars().first()
        if not rec:
            raise HTTPException(status_code=404, detail="Recruiter not found")
        
        # Update fields
        if req.name is not None:
            rec.name = req.name
        if req.email is not None:
            # Check if email already exists
            existing = db.execute(select(Recruiter).where(Recruiter.email == req.email, Recruiter.id != recruiter_id)).scalars().first()
            if existing:
                raise HTTPException(status_code=400, detail="Email already in use")
            rec.email = req.email
        if req.role is not None:
            rec.role = req.role
        if req.password is not None:
            rec.hashed_password = get_password_hash(req.password)
        
        db.commit()
        db.refresh(rec)
        
        # Get counts
        jobs_count = db.execute(
            select(func.count()).select_from(Job).where(Job.recruiter_id == rec.id)
        ).scalar() or 0
        
        candidates_count = db.execute(
            select(func.count()).select_from(Candidate).where(Candidate.recruiter_id == rec.id)
        ).scalar() or 0
        
        return AdminRecruiterResponse(
            id=rec.id,
            email=rec.email,
            name=rec.name,
            role=rec.role,
            jobs_count=jobs_count,
            candidates_count=candidates_count,
            created_at=rec.created_at.isoformat(),
        )

@app.delete("/admin/recruiters/{recruiter_id}")
async def admin_delete_recruiter(
    recruiter_id: int,
    recruiter: dict = Depends(require_admin),
) -> dict:
    """Delete a recruiter (admin only)."""
    from sqlalchemy import select, func, delete
    
    with get_session() as db:
        rec = db.execute(select(Recruiter).where(Recruiter.id == recruiter_id)).scalars().first()
        if not rec:
            raise HTTPException(status_code=404, detail="Recruiter not found")
        
        # Prevent deleting yourself
        current_recruiter_id = recruiter.get("recruiter_id")
        if current_recruiter_id == recruiter_id:
            raise HTTPException(status_code=400, detail="Cannot delete your own account")
        
        # Check for associated data
        jobs_count = db.execute(select(func.count()).select_from(Job).where(Job.recruiter_id == recruiter_id)).scalar() or 0
        candidates_count = db.execute(select(func.count()).select_from(Candidate).where(Candidate.recruiter_id == recruiter_id)).scalar() or 0
        
        if jobs_count > 0 or candidates_count > 0:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot delete recruiter with {jobs_count} jobs and {candidates_count} candidates. Reassign or delete them first."
            )
        
        db.delete(rec)
        db.commit()
    
    return {"status": "deleted", "id": recruiter_id}

@app.put("/admin/candidates/{candidate_id}", response_model=AdminCandidateResponse)
async def admin_update_candidate(
    candidate_id: str,
    req: AdminUpdateCandidateRequest,
    recruiter: dict = Depends(require_admin),
) -> AdminCandidateResponse:
    """Update a candidate (admin only)."""
    from sqlalchemy import select, func
    
    with get_session() as db:
        cand = db.execute(select(Candidate).where(Candidate.id == candidate_id)).scalars().first()
        if not cand:
            raise HTTPException(status_code=404, detail="Candidate not found")
        
        # Update fields
        if req.name is not None:
            cand.name = req.name
        if req.email is not None:
            # Check if email already exists
            existing = db.execute(select(Candidate).where(Candidate.email == req.email, Candidate.id != candidate_id)).scalars().first()
            if existing:
                raise HTTPException(status_code=400, detail="Email already in use")
            cand.email = req.email
        if req.category is not None:
            cand.category = req.category
        if req.recruiter_id is not None:
            # Verify recruiter exists
            if req.recruiter_id != 0:  # 0 means unassign
                rec = db.execute(select(Recruiter).where(Recruiter.id == req.recruiter_id)).scalars().first()
                if not rec:
                    raise HTTPException(status_code=404, detail="Recruiter not found")
                cand.recruiter_id = req.recruiter_id
            else:
                cand.recruiter_id = None
        
        db.commit()
        db.refresh(cand)
        
        # Get recruiter email
        recruiter_email = None
        if cand.recruiter_id:
            rec = db.execute(select(Recruiter).where(Recruiter.id == cand.recruiter_id)).scalars().first()
            recruiter_email = rec.email if rec else None
        
        # Parse skills
        skills = None
        if cand.skills:
            try:
                skills = json.loads(cand.skills) if isinstance(cand.skills, str) else cand.skills
            except:
                skills = None
        
        return AdminCandidateResponse(
            id=cand.id,
            name=cand.name,
            email=cand.email,
            category=cand.category,
            recruiter_id=cand.recruiter_id,
            recruiter_email=recruiter_email,
            skills=skills,
            created_at=cand.created_at.isoformat(),
        )

@app.delete("/admin/candidates/{candidate_id}")
async def admin_delete_candidate(
    candidate_id: str,
    recruiter: dict = Depends(require_admin),
) -> dict:
    """Delete a candidate (admin only)."""
    from sqlalchemy import select, delete
    
    with get_session() as db:
        cand = db.execute(select(Candidate).where(Candidate.id == candidate_id)).scalars().first()
        if not cand:
            raise HTTPException(status_code=404, detail="Candidate not found")
        
        # Delete associated scores
        db.execute(delete(CandidateScore).where(CandidateScore.candidate_id == candidate_id))
        
        # Delete candidate
        db.delete(cand)
        db.commit()
    
    return {"status": "deleted", "id": candidate_id}
