"""Seed jobs for each ML dataset category."""
import sys
import os
sys.path.append(os.path.join(os.getcwd(), "backend"))
os.environ["DATABASE_URL"] = "sqlite:///./guidance_demo.db"

from backend.database import get_session
from backend.models import Job
from sqlalchemy import select

# Jobs matching ML dataset categories
JOBS = [
    {
        "id": "job-advocate",
        "title": "Legal Advocate",
        "category": "Advocate",
        "description": "Legal professional role focusing on litigation and client representation.",
        "required_skills": "legal research,litigation,contract drafting,negotiation,court procedures",
        "min_years_experience": 3.0,
    },
    {
        "id": "job-arts",
        "title": "Visual Artist",
        "category": "Arts",
        "description": "Creative role focusing on visual arts, illustration, and design.",
        "required_skills": "illustration,painting,digital art,graphic design,creativity",
        "min_years_experience": 2.0,
    },
    {
        "id": "job-datascience",
        "title": "Data Scientist",
        "category": "Data Science",
        "description": "Data analysis and machine learning role using Python and statistical methods.",
        "required_skills": "python,machine learning,sql,statistics,pandas,numpy,scikit-learn",
        "min_years_experience": 2.0,
    },
    {
        "id": "job-hr",
        "title": "HR Manager",
        "category": "HR",
        "description": "Human Resources management including recruitment, employee relations, and policy.",
        "required_skills": "recruitment,employee relations,hris,performance management,labor law",
        "min_years_experience": 4.0,
    },
    {
        "id": "job-mecheng",
        "title": "Mechanical Engineer",
        "category": "Mechanical Engineer",
        "description": "Engineering role focusing on mechanical design, CAD, and manufacturing.",
        "required_skills": "cad,solidworks,autocad,thermodynamics,manufacturing,gd&t",
        "min_years_experience": 3.0,
    },
    {
        "id": "job-webdesign",
        "title": "Web Designer",
        "category": "Web Designing",
        "description": "Frontend web design and development with focus on UI/UX.",
        "required_skills": "html,css,javascript,figma,ui/ux,responsive design",
        "min_years_experience": 2.0,
    },
]


def seed_jobs():
    print("Seeding jobs for ML categories...\n")
    
    with get_session() as db:
        # Remove existing seeded jobs
        for job_data in JOBS:
            existing = db.execute(select(Job).where(Job.id == job_data["id"])).scalars().first()
            if existing:
                db.delete(existing)
        db.commit()
        
        # Create new jobs
        for job_data in JOBS:
            job = Job(**job_data)
            db.add(job)
            print(f"  Added: {job_data['title']} ({job_data['category']})")
        
        db.commit()
    
    print("\nDone! Jobs seeded for all ML categories.")


if __name__ == "__main__":
    seed_jobs()
