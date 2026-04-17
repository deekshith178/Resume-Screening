from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from backend.models import Job, CandidateScore, Candidate

engine = create_engine('sqlite:///./guidance_demo.db')

with Session(engine) as session:
    # 1. Find Web Designer job
    jobs = session.scalars(select(Job).where(Job.title.ilike("%Web Design%"))).all()
    
    for job in jobs:
        print(f"\nJob: {job.title} (ID: {job.id})")
        
        # 2. Get scores
        scores = session.scalars(select(CandidateScore).where(CandidateScore.job_id == job.id)).all()
        print(f"Total Scores found: {len(scores)}")
        
        for s in scores:
            c = session.scalar(select(Candidate).where(Candidate.id == s.candidate_id))
            print(f"  - Candidate: {c.name} (ID: {s.candidate_id})")
            print(f"    Score: {s.score}")
            print(f"    Selected: {s.is_selected}")
            print(f"    Resume Path: {c.resume_path}")
            print(f"    Components: {s.components_json}")
