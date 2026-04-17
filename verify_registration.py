
import sys
import os
import asyncio
from fastapi.testclient import TestClient

# Ensure backend dir is in path
sys.path.append(os.path.join(os.getcwd(), "backend"))
os.environ["DATABASE_URL"] = "sqlite:///./guidance_demo.db" 

from backend.main import app, Recruiter
from backend.database import get_session
from sqlalchemy import delete

client = TestClient(app)

def verify_registration():
    email = "new.recruiter@example.com"
    password = "NewPassword123!"
    
    print(f"Testing registration for: {email}")
    
    # Cleaning up first
    with get_session() as db:
        db.execute(delete(Recruiter).where(Recruiter.email == email))
        db.commit()

    # Register
    print("Sending registration request...")
    response = client.post("/auth/recruiter/register", json={
        "email": email,
        "password": password
    })
    
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print("Success! Response:", data)
        if "access_token" in data and data["email"] == email:
             print("PASS: Token received and email matches.")
        else:
             print("FAIL: Response malformed.")
    else:
        print("FAIL: Registration failed.")
        print(response.json())

    # Verify duplicates
    print("\nTesting duplicate registration...")
    response_dup = client.post("/auth/recruiter/register", json={
        "email": email,
        "password": password
    })
    print(f"Duplicate Status Code: {response_dup.status_code} (Expected 400)")
    if response_dup.status_code == 400:
        print("PASS: Duplicate rejected correctly.")
    else:
        print("FAIL: Duplicate not handled correctly.")
    
    # Cleanup
    with get_session() as db:
        db.execute(delete(Recruiter).where(Recruiter.email == email))
        db.commit()

if __name__ == "__main__":
    verify_registration()
