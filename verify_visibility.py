
import requests
import sys

BASE_URL = "http://localhost:8000"

def register_recruiter(email, password, name="Test Recruiter"):
    print(f"\n[Registering] {email}...")
    try:
        resp = requests.post(f"{BASE_URL}/auth/recruiter/register", json={
            "email": email,
            "password": password,
            "name": name
        })
        if resp.status_code == 200:
            print("  Success!")
            return resp.json()
        elif resp.status_code == 400 and "already registered" in resp.text:
            print("  Already registered, trying login...")
            return login(email, password)
        else:
            print(f"  Failed: {resp.text}")
            return None
    except Exception as e:
        print(f"  Error: {e}")
        return None

def login(email, password):
    print(f"\n[Login] {email}...")
    try:
        resp = requests.post(f"{BASE_URL}/auth/recruiter/login", json={
            "username": email,
            "password": password
        })
        if resp.status_code == 200:
            print("  Success!")
            return resp.json()
        else:
            print(f"  Failed: {resp.text}")
            return None
    except Exception as e:
        print(f"  Error: {e}")
        return None

def list_jobs(token):
    print(f"\n[List Jobs] Fetching jobs...")
    try:
        resp = requests.get(f"{BASE_URL}/jobs", headers={"Authorization": f"Bearer {token}"})
        if resp.status_code == 200:
            data = resp.json()
            jobs = data["items"]
            print(f"  Found {len(jobs)} jobs:")
            for j in jobs:
                print(f"    - [{j['id']}] {j['title']} (Category: {j['category']})")
            return jobs
        else:
            print(f"  Failed: {resp.text}")
            return []
    except Exception as e:
        print(f"  Error: {e}")
        return []

def main():
    # 1. Login as test@example.com (Admin/Dev) to see what SHOULD be there
    print("--- 1. Checking as Admin (test@example.com) ---")
    admin_auth = login("test@example.com", "password123")
    if not admin_auth:
        print("CRITICAL: Cannot login as test user. Is backend running?")
        sys.exit(1)
    
    admin_jobs = list_jobs(admin_auth["access_token"])
    
    # 2. Register/Login as a new recruiter
    print("\n--- 2. Checking as New Recruiter (new@example.com) ---")
    user_email = "new@example.com"
    user_pass = "password123"
    
    user_auth = register_recruiter(user_email, user_pass)
    if not user_auth:
        print("CRITICAL: Cannot authenticate new user.")
        sys.exit(1)
        
    user_jobs = list_jobs(user_auth["access_token"])
    
    # 3. Compare
    print("\n--- Summary ---")
    print(f"Admin sees {len(admin_jobs)} jobs.")
    print(f"New User sees {len(user_jobs)} jobs.")
    
    if len(user_jobs) < len(admin_jobs):
        print("ISSUE VERIFIED: New user sees fewer jobs than admin.")
        # Identify missing jobs
        user_job_ids = {j['id'] for j in user_jobs}
        missing = [j for j in admin_jobs if j['id'] not in user_job_ids]
        print("Missing jobs for new user:")
        for m in missing:
            print(f"  - {m['id']}")
    else:
        print("No issue detected? (Or admin has no extra jobs)")

if __name__ == "__main__":
    main()
