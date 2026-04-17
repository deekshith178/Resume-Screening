
import sys
import os
import asyncio
from typing import Optional

# Ensure backend dir is in path
sys.path.append(os.path.join(os.getcwd(), "backend"))

# Mock environment if needed (though we want real DB)
os.environ["DATABASE_URL"] = "sqlite:///./guidance_demo.db" 

from backend.database import get_session, engine, Base
from backend.models import Recruiter, Candidate
from backend.security import get_password_hash, verify_recruiter_credentials, generate_candidate_token, hash_token, verify_token
from sqlalchemy import select, delete

# Setup
def setup_db():
    print("Setting up database...")
    Base.metadata.create_all(bind=engine)

def create_test_recruiter(email: str, password: str):
    print(f"Creating/Updating test recruiter: {email}")
    with get_session() as db:
        # Cleanup first
        existing = db.execute(select(Recruiter).where(Recruiter.email == email)).scalars().first()
        if existing:
            db.delete(existing)
            db.commit()
        
        # Create new
        new_recruiter = Recruiter(
            email=email,
            hashed_password=get_password_hash(password),
            role="recruiter"
        )
        db.add(new_recruiter)
        db.commit()
    print("Test recruiter created.")

def create_test_candidate(email: str, name: str) -> str:
    print(f"Creating/Updating test candidate: {email}")
    candidate_id = "test_cand_real_auth"
    with get_session() as db:
        # Cleanup first
        existing = db.execute(select(Candidate).where(Candidate.email == email)).scalars().first()
        if existing:
             db.delete(existing)
        
        # Also check by ID
        existing_id = db.execute(select(Candidate).where(Candidate.id == candidate_id)).scalars().first()
        if existing_id:
            db.delete(existing_id)
        
        db.commit()

        # Create new
        new_cand = Candidate(
            id=candidate_id,
            email=email,
            name=name,
            resume_path="tests/data/sample_resume.txt", # Dummy path
            category="General"
        )
        db.add(new_cand)
        db.commit()
    print("Test candidate created.")
    return candidate_id

def verify_recruiter_login_logic(email: str, password: str):
    print(f"\n--- Verifying Recruiter Login Logic for {email} ---")
    
    # 1. Test with CORRECT credentials
    is_valid = verify_recruiter_credentials(email, password)
    print(f"Login with CORRECT password: {'PASS' if is_valid else 'FAIL'}")
    
    # 2. Test with INCORRECT password
    is_valid_bad = verify_recruiter_credentials(email, "wrongpassword")
    print(f"Login with WRONG password: {'PASS' if not is_valid_bad else 'FAIL (Should be False)'}")

def verify_candidate_token_logic(email: str):
    print(f"\n--- Verifying Candidate Token Logic for {email} ---")
    
    # Simulating request_candidate_token endpoint logic (without the bypass)
    with get_session() as db:
        cand = db.execute(select(Candidate).where(Candidate.email == email)).scalars().first()
        if not cand:
            print("FAIL: Candidate not found in DB.")
            return

        # Generate token
        raw_token = generate_candidate_token()
        print(f"Generated Raw Token: {raw_token}")
        
        # Hash and save
        cand.token_hash = hash_token(raw_token)
        db.add(cand)
        db.commit()
        print("Token hash saved to DB.")
        
        # Refresh to ensure we read back correctly
        db.refresh(cand)
        saved_hash = cand.token_hash
        
    # Verify the token (Simulating candidate_login and verify_token)
    print("Verifying token against DB hash...")
    is_valid = verify_token(raw_token, saved_hash)
    print(f"Token Verification: {'PASS' if is_valid else 'FAIL'}")
    
    # Verify BAD token
    is_valid_bad = verify_token("bad-token-string", saved_hash)
    print(f"Bad Token Verification: {'PASS' if not is_valid_bad else 'FAIL (Should be False)'}")


def cleanup(recruiter_email, candidate_email):
    print("\nCleaning up...")
    with get_session() as db:
        db.execute(delete(Recruiter).where(Recruiter.email == recruiter_email))
        db.execute(delete(Candidate).where(Candidate.email == candidate_email))
        db.commit()
    print("Cleanup done.")

if __name__ == "__main__":
    setup_db()
    
    TEST_REC_EMAIL = "real.recruiter@example.com"
    TEST_REC_PASS = "SecretPass123!"
    
    TEST_CAND_EMAIL = "real.candidate@example.com"
    
    try:
        # Setup Data
        create_test_recruiter(TEST_REC_EMAIL, TEST_REC_PASS)
        create_test_candidate(TEST_CAND_EMAIL, "Real Candidate")
        
        # Test Logic
        verify_recruiter_login_logic(TEST_REC_EMAIL, TEST_REC_PASS)
        verify_candidate_token_logic(TEST_CAND_EMAIL)
        
    except Exception as e:
        print(f"An error occurred: {e}")
        import traceback
        traceback.print_exc()
    finally:
        cleanup(TEST_REC_EMAIL, TEST_CAND_EMAIL)
