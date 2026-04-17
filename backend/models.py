from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class Candidate(Base):
    __tablename__ = "candidates"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    email: Mapped[str] = mapped_column(String, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    resume_path: Mapped[str] = mapped_column(String, nullable=False)
    category: Mapped[str] = mapped_column(String, nullable=False)

    # Optional cached skills / summary (text or JSON-serialized)
    skills: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Auth token hash
    token_hash: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    # Recruiter ownership
    recruiter_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("recruiters.id"), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    recruiter: Mapped[Optional["Recruiter"]] = relationship("Recruiter", back_populates="candidates")
    guidance_optins: Mapped[List["GuidanceOptIn"]] = relationship(back_populates="candidate")
    guidance_recommendations: Mapped[List["GuidanceRecommendation"]] = relationship(
        back_populates="candidate"
    )


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    category: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Simple comma-separated required skills for now
    required_skills: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    min_years_experience: Mapped[float] = mapped_column(Float, default=0.0)

    # Recruiter ownership
    recruiter_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("recruiters.id"), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    recruiter: Mapped[Optional["Recruiter"]] = relationship("Recruiter", back_populates="jobs")
    guidance_optins: Mapped[List["GuidanceOptIn"]] = relationship(back_populates="job")
    guidance_recommendations: Mapped[List["GuidanceRecommendation"]] = relationship(
        back_populates="job"
    )


class GuidanceOptIn(Base):
    __tablename__ = "guidance_optins"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    candidate_id: Mapped[str] = mapped_column(String, ForeignKey("candidates.id"), nullable=False)
    job_id: Mapped[str] = mapped_column(String, ForeignKey("jobs.id"), nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    candidate: Mapped[Candidate] = relationship(back_populates="guidance_optins")
    job: Mapped[Job] = relationship(back_populates="guidance_optins")


class GuidanceRecommendation(Base):
    __tablename__ = "guidance_recommendations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    candidate_id: Mapped[str] = mapped_column(String, ForeignKey("candidates.id"), nullable=False)
    job_id: Mapped[str] = mapped_column(String, ForeignKey("jobs.id"), nullable=False)

    # JSON-serialized lists (e.g. via json.dumps)
    missing_skills_json: Mapped[str] = mapped_column(Text, nullable=False)
    resources_json: Mapped[str] = mapped_column(Text, nullable=False)

    delivered: Mapped[bool] = mapped_column(Boolean, default=False)
    delivery_channel: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    candidate: Mapped[Candidate] = relationship(back_populates="guidance_recommendations")
    job: Mapped[Job] = relationship(back_populates="guidance_recommendations")




class Recruiter(Base):
    __tablename__ = "recruiters"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    role: Mapped[str] = mapped_column(String, default="recruiter")
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    jobs: Mapped[List["Job"]] = relationship("Job", back_populates="recruiter")
    candidates: Mapped[List["Candidate"]] = relationship("Candidate", back_populates="recruiter")


class CandidateScore(Base):
    """Stores scores for candidates matched to jobs."""
    __tablename__ = "candidate_scores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    candidate_id: Mapped[str] = mapped_column(String, ForeignKey("candidates.id"), nullable=False)
    job_id: Mapped[str] = mapped_column(String, ForeignKey("jobs.id"), nullable=False)
    
    score: Mapped[float] = mapped_column(Float, nullable=False)
    is_selected: Mapped[bool] = mapped_column(Boolean, default=False)
    is_override: Mapped[bool] = mapped_column(Boolean, default=False)  # True if manually overridden
    
    # Store score components as JSON
    components_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    candidate: Mapped[Candidate] = relationship("Candidate")
    job: Mapped[Job] = relationship("Job")


class AuditLog(Base):
    """Audit logs for recruiter actions (overrides, publishes, etc.)."""
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    action: Mapped[str] = mapped_column(String, nullable=False)  # e.g., "override", "publish", "create_job"
    recruiter_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    job_id: Mapped[Optional[str]] = mapped_column(String, ForeignKey("jobs.id"), nullable=True)
    candidate_id: Mapped[Optional[str]] = mapped_column(String, ForeignKey("candidates.id"), nullable=True)
    
    # JSON metadata for additional context
    metadata_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
