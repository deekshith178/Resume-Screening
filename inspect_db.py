
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from backend.models import Job, Base

def inspect_jobs():
    engine = create_engine("sqlite:///./guidance_demo.db")
    Session = sessionmaker(bind=engine)
    session = Session()

    jobs = session.query(Job).all()
    print(f"Total jobs: {len(jobs)}")
    for j in jobs:
        print(f"ID: {j.id}, RecruiterID: {j.recruiter_id}, Title: {j.title}")

if __name__ == "__main__":
    inspect_jobs()
