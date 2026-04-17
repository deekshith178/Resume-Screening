
import requests
import sys

BASE_URL = "http://localhost:8000"

def login(email, password):
    print(f"\n[Login] {email}...")
    try:
        resp = requests.post(f"{BASE_URL}/auth/recruiter/login", json={
            "username": email,
            "password": password
        })
        if resp.status_code == 200:
            return resp.json()
        print(f"  Failed: {resp.text}")
        return None
    except Exception as e:
        print(f"  Error: {e}")
        return None

def main():
    # 1. Login as new recruiter
    print("--- Checking permissions for new@example.com ---")
    user_auth = login("new@example.com", "password123")
    if not user_auth:
        print("CRITICAL: Cannot authenticate. Run verify_visibility.py first to register user?")
        sys.exit(1)
        
    token = user_auth["access_token"]
    
    # 2. Try to access 'job-webdesign' (which should belong to admin or seed data)
    job_id = "job-webdesign"
    print(f"\n[Request] Shortlist for '{job_id}' (owned by other/admin)...")
    
    resp = requests.get(f"{BASE_URL}/jobs/{job_id}/shortlist", headers={"Authorization": f"Bearer {token}"})
    
    if resp.status_code == 200:
        data = resp.json()
        print("  SUCCESS! Access granted.")
        print(f"  Candidates visible: {len(data['candidates'])}")
        # Ideally this should be 0 if the new recruiter hasn't added anyone
        if len(data['candidates']) == 0:
             print("  Verification PASSED: Access granted, but privacy filter active (0 candidates seen).")
        else:
             print(f"  Warning: Saw {len(data['candidates'])} candidates. Are they yours?")
    elif resp.status_code == 403:
        print("  FAILED: 403 Forbidden (Logic not fixed)")
    else:
        print(f"  FAILED: {resp.status_code} - {resp.text}")

if __name__ == "__main__":
    main()
