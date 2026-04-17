"""Script to initialize database and create test candidate for login testing."""
import sys
from pathlib import Path
import uuid
import secrets
import hashlib

# Add backend directory to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Now we can import from the backend package structure
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
from datetime import datetime

# Create engine directly
DATABASE_URL = "sqlite:///./hireflow.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Define models inline to avoid import issues
class Candidate(Base):
    __tablename__ = "candidates"
    id = Column(String, primary_key=True)
    email = Column(String, nullable=False)
    name = Column(String, nullable=False)
    resume_path = Column(String, nullable=False)
    category = Column(String, nullable=False)
    skills = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)
    token_hash = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Job(Base):
    __tablename__ = "jobs"
    id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    category = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    required_skills = Column(Text, nullable=True)
    min_years_experience = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)

class Recruiter(Base):
    __tablename__ = "recruiters"
    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="recruiter")
    created_at = Column(DateTime, default=datetime.utcnow)

class GuidanceOptIn(Base):
    __tablename__ = "guidance_optins"
    id = Column(Integer, primary_key=True, autoincrement=True)
    candidate_id = Column(String, ForeignKey("candidates.id"), nullable=False)
    job_id = Column(String, ForeignKey("jobs.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class GuidanceRecommendation(Base):
    __tablename__ = "guidance_recommendations"
    id = Column(Integer, primary_key=True, autoincrement=True)
    candidate_id = Column(String, ForeignKey("candidates.id"), nullable=False)
    job_id = Column(String, ForeignKey("jobs.id"), nullable=False)
    missing_skills_json = Column(Text, nullable=False)
    resources_json = Column(Text, nullable=False)
    delivered = Column(Boolean, default=False)
    delivery_channel = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class CandidateScore(Base):
    __tablename__ = "candidate_scores"
    id = Column(Integer, primary_key=True, autoincrement=True)
    candidate_id = Column(String, ForeignKey("candidates.id"), nullable=False)
    job_id = Column(String, ForeignKey("jobs.id"), nullable=False)
    score = Column(Float, nullable=False)
    is_selected = Column(Boolean, default=False)
    is_override = Column(Boolean, default=False)
    components_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    action = Column(String, nullable=False)
    recruiter_id = Column(String, nullable=True)
    job_id = Column(String, ForeignKey("jobs.id"), nullable=True)
    candidate_id = Column(String, ForeignKey("candidates.id"), nullable=True)
    metadata_json = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()

def generate_candidate_token() -> str:
    return secrets.token_urlsafe(32)

def get_password_hash(password: str) -> str:
    # Simple hash for demo purposes
    return hashlib.sha256(password.encode()).hexdigest()

# Create all tables
print("Creating database tables...")
Base.metadata.create_all(bind=engine)
print("Tables created successfully!")

# Create test data
db = SessionLocal()

try:
    # Check if test candidate exists
    existing = db.query(Candidate).filter(Candidate.email == "alice@example.com").first()
    if existing:
        print(f"Test candidate already exists: {existing.email} (ID: {existing.id})")
        # Generate new token for login
        raw_token = generate_candidate_token()
        existing.token_hash = hash_token(raw_token)
        db.commit()
        print(f"Updated token for login: {raw_token}")
    else:
        # Generate a token for the candidate
        raw_token = generate_candidate_token()
        hashed = hash_token(raw_token)
        
        # Create test candidate
        candidate = Candidate(
            id=str(uuid.uuid4()),
            email="alice@example.com",
            name="Alice Johnson",
            resume_path="/resumes/alice_resume.pdf",
            category="Software Engineer",
            skills="Python, JavaScript, React, FastAPI",
            summary="Experienced software engineer with 5 years of experience",
            token_hash=hashed
        )
        db.add(candidate)
        db.commit()
        db.refresh(candidate)
        print(f"\nCreated test candidate:")
        print(f"  Name: {candidate.name}")
        print(f"  Email: {candidate.email}")
        print(f"  ID: {candidate.id}")
        print(f"  Token (save this for login): {raw_token}")

    # Check if test job exists
    existing_job = db.query(Job).filter(Job.id == "test-job-1").first()
    if existing_job:
        print(f"\nTest job already exists: {existing_job.title}")
    else:
        # Create test job
        job = Job(
            id="test-job-1",
            title="Senior Software Engineer",
            category="Software Engineer",
            description="Looking for experienced software engineers",
            required_skills="Python, JavaScript, React",
            min_years_experience=3.0
        )
        db.add(job)
        db.commit()
        print(f"\nCreated test job: {job.title}")

    # Check if test recruiter exists
    existing_recruiter = db.query(Recruiter).filter(Recruiter.email == "admin@hireflow.com").first()
    if existing_recruiter:
        print(f"\nTest recruiter already exists: {existing_recruiter.email}")
    else:
        # Create test recruiter
        recruiter = Recruiter(
            email="admin@hireflow.com",
            hashed_password=get_password_hash("admin123"),
            role="admin"
        )
        db.add(recruiter)
        db.commit()
        print(f"\nCreated test recruiter: admin@hireflow.com (password: admin123)")

    # List all candidates
    print("\n--- All candidates in database ---")
    candidates = db.query(Candidate).all()
    for c in candidates:
        print(f"  {c.email} - {c.name} (ID: {c.id})")

finally:
    db.close()

print("\nDone! Database is ready for testing.")
