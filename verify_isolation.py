"""Verify recruiter data isolation works correctly."""
import sys
import os
sys.path.append(os.path.join(os.getcwd(), "backend"))
os.environ["DATABASE_URL"] = "sqlite:///./guidance_demo.db"

from fastapi.testclient import TestClient
from backend.main import app
from backend.database import get_session
from backend.models import Recruiter, Job
from backend.security import get_password_hash
from sqlalchemy import delete

client = TestClient(app)

def test_isolation():
    print("=== Testing Recruiter Data Isolation ===\n")
    
    # Clean up test data
    with get_session() as db:
        db.execute(delete(Job).where(Job.id.like("test-%")))
        db.execute(delete(Recruiter).where(Recruiter.email.like("test%")))
        db.commit()
    
    # Create two test recruiters
    print("1. Creating two test recruiters...")
    with get_session() as db:
        r1 = Recruiter(email="test1@example.com", hashed_password=get_password_hash("pass1"), role="recruiter")
        r2 = Recruiter(email="test2@example.com", hashed_password=get_password_hash("pass2"), role="recruiter")
        db.add_all([r1, r2])
        db.commit()
        db.refresh(r1)
        db.refresh(r2)
        r1_id, r2_id = r1.id, r2.id
    print(f"   Recruiter 1 ID: {r1_id}")
    print(f"   Recruiter 2 ID: {r2_id}")
    
    # Login as recruiter 1
    print("\n2. Logging in as Recruiter 1...")
    resp1 = client.post("/auth/recruiter/login", json={"username": "test1@example.com", "password": "pass1"})
    token1 = resp1.json()["access_token"]
    print(f"   Token obtained: {token1[:20]}...")
    
    # Create job as recruiter 1
    print("\n3. Creating job as Recruiter 1...")
    resp = client.post("/jobs", 
        headers={"Authorization": f"Bearer {token1}"},
        json={"id": "test-job-r1", "title": "R1 Job", "category": "Engineering", "description": "Test"}
    )
    print(f"   Job created: {resp.json()}")
    
    # Login as recruiter 2
    print("\n4. Logging in as Recruiter 2...")
    resp2 = client.post("/auth/recruiter/login", json={"username": "test2@example.com", "password": "pass2"})
    token2 = resp2.json()["access_token"]
    
    # Create job as recruiter 2
    print("\n5. Creating job as Recruiter 2...")
    resp = client.post("/jobs",
        headers={"Authorization": f"Bearer {token2}"},
        json={"id": "test-job-r2", "title": "R2 Job", "category": "Marketing", "description": "Test"}
    )
    print(f"   Job created: {resp.json()}")
    
    # List jobs as recruiter 1 - should only see their job
    print("\n6. Listing jobs as Recruiter 1...")
    resp = client.get("/jobs", headers={"Authorization": f"Bearer {token1}"})
    data1 = resp.json()
    print(f"   Response: {data1}")
    jobs1 = data1.get("jobs", [])
    print(f"   Jobs visible: {[j['id'] for j in jobs1]}")
    
    # List jobs as recruiter 2 - should only see their job
    print("\n7. Listing jobs as Recruiter 2...")
    resp = client.get("/jobs", headers={"Authorization": f"Bearer {token2}"})
    data2 = resp.json()
    print(f"   Response: {data2}")
    jobs2 = data2.get("jobs", [])
    print(f"   Jobs visible: {[j['id'] for j in jobs2]}")
    
    # Verify isolation
    print("\n=== RESULTS ===")
    r1_sees_only_own = all(j["id"].startswith("test-job-r1") for j in jobs1 if j["id"].startswith("test-"))
    r2_sees_only_own = all(j["id"].startswith("test-job-r2") for j in jobs2 if j["id"].startswith("test-"))
    
    if r1_sees_only_own and r2_sees_only_own:
        print("✓ PASS: Data isolation working correctly!")
    else:
        print("✗ FAIL: Data isolation NOT working")
        print(f"  R1 jobs: {[j['id'] for j in jobs1]}")
        print(f"  R2 jobs: {[j['id'] for j in jobs2]}")
    
    # Cleanup
    with get_session() as db:
        db.execute(delete(Job).where(Job.id.like("test-%")))
        db.execute(delete(Recruiter).where(Recruiter.email.like("test%")))
        db.commit()
    print("\nTest data cleaned up.")

if __name__ == "__main__":
    test_isolation()
