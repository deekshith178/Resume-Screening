
import requests
import sys

BASE_URL = "http://localhost:8000"

def register_and_check():
    # 1. Register new user
    email = "newuser@example.com"
    password = "password123"
    
    # Try login first to see if exists
    login_resp = requests.post(f"{BASE_URL}/auth/recruiter/login", json={"username": email, "password": password})
    
    token = None
    if login_resp.status_code == 200:
        print(f"User {email} already exists, logging in...")
        token = login_resp.json()["access_token"]
    else:
        print(f"Registering {email}...")
        reg_resp = requests.post(f"{BASE_URL}/auth/recruiter/register", json={"email": email, "password": password})
        if reg_resp.status_code != 200:
            print(f"Registration failed: {reg_resp.text}")
            return
        token = reg_resp.json()["access_token"]

    print(f"Token obtained for {email}")
    
    # 2. List jobs
    headers = {"Authorization": f"Bearer {token}"}
    jobs_resp = requests.get(f"{BASE_URL}/jobs", headers=headers)
    
    if jobs_resp.status_code == 200:
        jobs = jobs_resp.json()["items"]
        print(f"Jobs for {email}: {len(jobs)}")
        for j in jobs:
            print(f" - {j['id']} ({j['title']})")
    else:
        print(f"Failed to list jobs: {jobs_resp.text}")

def check_admin_bypass():
    # 3. Check admin bypass
    print("\nChecking admin bypass...")
    login_resp = requests.post(f"{BASE_URL}/auth/recruiter/login", json={"username": "test@example.com", "password": "password123"})
    if login_resp.status_code == 200:
        token = login_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        jobs_resp = requests.get(f"{BASE_URL}/jobs", headers=headers)
        if jobs_resp.status_code == 200:
            jobs = jobs_resp.json()["items"]
            print(f"Jobs for test@example.com (bypass): {len(jobs)}")
            for j in jobs:
                print(f" - {j['id']} ({j['title']})")
        else:
            print(f"Failed to list jobs for admin: {jobs_resp.text}")
    else:
        print(f"Admin login failed: {login_resp.text}")

if __name__ == "__main__":
    try:
        # Check health
        try:
            requests.get(f"{BASE_URL}/health")
        except requests.exceptions.ConnectionError:
            print("Backend is NOT running on localhost:8000")
            sys.exit(1)

        register_and_check()
        check_admin_bypass()
    except Exception as e:
        print(f"Error: {e}")
