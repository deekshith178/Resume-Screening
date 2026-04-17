import requests
import sys

BASE_URL = "http://localhost:8000"
EMAIL = "demo.candidate@example.com"

def test_flow():
    print(f"Testing Candidate Auth Flow for {EMAIL}")
    
    # 1. Request Token
    print("1. Requesting Token...")
    try:
        req_resp = requests.post(f"{BASE_URL}/auth/candidate/request-token", json={"email": EMAIL})
        if req_resp.status_code != 200:
            print(f"FAILED to request token: {req_resp.status_code} {req_resp.text}")
            return
        
        data = req_resp.json()
        print(f"   Success! Received: {data}")
        token = data.get("token")
        cand_id = data.get("candidate_id")
        
        if not token or not cand_id:
            print("FAILED: Missing token or candidate_id")
            return

    except Exception as e:
        print(f"FAILED connection: {e}")
        return

    # 2. Login with Token
    print(f"2. Logging in with token: {token[:10]}...")
    try:
        login_resp = requests.post(f"{BASE_URL}/candidate/login", json={"candidate_id": cand_id, "token": token})
        if login_resp.status_code != 200:
            print(f"FAILED login: {login_resp.status_code} {login_resp.text}")
            return
        
        login_data = login_resp.json()
        print(f"   Success! Status: {login_data}")

    except Exception as e:
         print(f"FAILED connection: {e}")
         return

    # 3. Fetch Status (Portal data)
    print("3. Fetching Status...")
    try:
        status_resp = requests.get(f"{BASE_URL}/candidate/{cand_id}/status", params={"token": token})
        if status_resp.status_code != 200:
            print(f"FAILED fetch status: {status_resp.status_code} {status_resp.text}")
            return
            
        print(f"   Success! Data: {status_resp.json()}")
        print("\nALL BACKEND TESTS PASSED")

    except Exception as e:
         print(f"FAILED connection: {e}")

if __name__ == "__main__":
    test_flow()
