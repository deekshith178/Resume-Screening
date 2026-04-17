"""Seed sample candidates for all job categories."""
import sys
import os
import json
import random
sys.path.append(os.path.join(os.getcwd(), "backend"))
os.environ["DATABASE_URL"] = "sqlite:///./guidance_demo.db"

from backend.database import get_session
from backend.models import Candidate, CandidateScore, Job
from sqlalchemy import select

# Sample candidate data for each category
SAMPLE_CANDIDATES = {
    "Advocate": [
        {"name": "Sarah Johnson", "email": "sarah.johnson@lawfirm.com", "skills": ["litigation", "contract law", "negotiation"]},
        {"name": "Michael Chen", "email": "m.chen@legal.com", "skills": ["corporate law", "mergers", "due diligence"]},
        {"name": "Emily Davis", "email": "emily.d@attorneys.com", "skills": ["family law", "mediation", "court procedures"]},
    ],
    "Arts": [
        {"name": "Luna Martinez", "email": "luna.art@creative.com", "skills": ["illustration", "digital art", "photoshop"]},
        {"name": "James Wilson", "email": "j.wilson@design.co", "skills": ["painting", "sculpture", "art direction"]},
        {"name": "Zoe Taylor", "email": "zoe.t@artworks.com", "skills": ["graphic design", "branding", "typography"]},
    ],
    "Data Science": [
        {"name": "Alex Kumar", "email": "alex.k@datatech.com", "skills": ["python", "machine learning", "sql"]},
        {"name": "Ryan Park", "email": "ryan.p@analytics.io", "skills": ["deep learning", "tensorflow", "statistics"]},
        {"name": "Sofia Rodriguez", "email": "sofia.r@mlcorp.com", "skills": ["pandas", "scikit-learn", "data visualization"]},
    ],
    "HR": [
        {"name": "Jennifer Brown", "email": "j.brown@hrpro.com", "skills": ["recruitment", "employee relations", "hris"]},
        {"name": "David Lee", "email": "d.lee@talentmgmt.com", "skills": ["performance management", "training", "compensation"]},
        {"name": "Amanda White", "email": "a.white@peoplefirst.com", "skills": ["labor law", "benefits", "onboarding"]},
    ],
    "Mechanical Engineer": [
        {"name": "Robert Zhang", "email": "r.zhang@engineering.com", "skills": ["cad", "solidworks", "thermodynamics"]},
        {"name": "Priya Sharma", "email": "p.sharma@mechdesign.com", "skills": ["autocad", "manufacturing", "fea"]},
        {"name": "Thomas Anderson", "email": "t.anderson@machines.io", "skills": ["gd&t", "prototyping", "matlab"]},
    ],
    "Web Designing": [
        {"name": "Chris Miller", "email": "chris.m@webdev.com", "skills": ["html", "css", "javascript"]},
        {"name": "Natalie Kim", "email": "n.kim@uxdesign.io", "skills": ["figma", "ui/ux", "responsive design"]},
        {"name": "Kevin Patel", "email": "k.patel@frontend.dev", "skills": ["react", "tailwind", "accessibility"]},
    ],
}

# Map category to job_id
CATEGORY_TO_JOB = {
    "Advocate": "job-advocate",
    "Arts": "job-arts",
    "Data Science": "job-datascience",
    "HR": "job-hr",
    "Mechanical Engineer": "job-mecheng",
    "Web Designing": "job-webdesign",
}


def seed_candidates():
    print("Seeding sample candidates for all jobs...\n")
    
    with get_session() as db:
        for category, candidates in SAMPLE_CANDIDATES.items():
            job_id = CATEGORY_TO_JOB.get(category)
            if not job_id:
                continue
                
            # Check if job exists
            job = db.execute(select(Job).where(Job.id == job_id)).scalars().first()
            if not job:
                print(f"  Job {job_id} not found, skipping {category}")
                continue
            
            print(f"  {category} ({job_id}):")
            
            for cand_data in candidates:
                # Check if candidate already exists
                existing = db.execute(
                    select(Candidate).where(Candidate.email == cand_data["email"])
                ).scalars().first()
                
                if existing:
                    candidate_id = existing.id
                    print(f"    - {cand_data['name']} (exists)")
                else:
                    # Create new candidate
                    candidate_id = f"cand_{cand_data['email'].split('@')[0]}"
                    candidate = Candidate(
                        id=candidate_id,
                        name=cand_data["name"],
                        email=cand_data["email"],
                        category=category,
                        skills=json.dumps(cand_data["skills"]),
                        recruiter_id=3,  # newrecruiter2@test.com
                        resume_path=f"data/sample_resumes/{category.lower().replace(' ', '_')}_sample.pdf",
                    )
                    db.add(candidate)
                    db.flush()
                    print(f"    + {cand_data['name']} (created)")
                
                # Check if score exists for this job
                existing_score = db.execute(
                    select(CandidateScore).where(
                        CandidateScore.candidate_id == candidate_id,
                        CandidateScore.job_id == job_id
                    )
                ).scalars().first()
                
                if not existing_score:
                    # Create score with random components
                    score = random.uniform(55, 95)
                    components = {
                        "normalized_similarity": random.uniform(0.6, 0.95),
                        "E_norm": random.uniform(0.3, 0.8),
                        "P_norm": random.uniform(0.2, 0.7),
                        "C_norm": random.uniform(0.1, 0.5),
                    }
                    
                    score_record = CandidateScore(
                        candidate_id=candidate_id,
                        job_id=job_id,
                        score=score,
                        components_json=json.dumps(components),
                    )
                    db.add(score_record)
        
        db.commit()
    
    print("\nDone! Sample candidates seeded for all jobs.")


if __name__ == "__main__":
    seed_candidates()
