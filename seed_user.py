
import sys
import os

# Ensure backend dir is in path
sys.path.append(os.path.join(os.getcwd(), "backend"))

# Mock environment to point to real file
os.environ["DATABASE_URL"] = "sqlite:///./guidance_demo.db" 

from backend.database import get_session, engine, Base
from backend.models import Recruiter
from backend.security import get_password_hash
from sqlalchemy import select

def seed_recruiter():
    email = "real.recruiter@example.com"
    password = "SecretPass123!"
    
    print(f"Seeding recruiter: {email}")
    
    Base.metadata.create_all(bind=engine)
    
    with get_session() as db:
        existing = db.execute(select(Recruiter).where(Recruiter.email == email)).scalars().first()
        if existing:
            print("User already exists. Reseting password.")
            existing.hashed_password = get_password_hash(password)
        else:
            print("Creating new user.")
            new_recruiter = Recruiter(
                email=email,
                hashed_password=get_password_hash(password),
                role="recruiter"
            )
            db.add(new_recruiter)
        db.commit()
    print("Seeding complete.")

if __name__ == "__main__":
    seed_recruiter()
