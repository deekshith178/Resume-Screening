import sys
import os
import asyncio
from unittest.mock import MagicMock

# Ensure backend dir is in path
sys.path.append(os.path.join(os.getcwd(), "backend"))

# Mock environment
os.environ["DATABASE_URL"] = "sqlite:///./guidance_demo.db"

try:
    from backend.main import candidate_login, request_candidate_token, CandidateLoginRequest, CandidateTokenRequest
except ImportError as e:
    print(f"Import Error: {e}")
    sys.exit(1)

async def verify_bypass():
    print("TESTING BYPASS LOGIC...")
    
    # 1. Test Request Token with demo email
    print("\n1. Requesting Token for 'demo.candidate@example.com'...")
    try:
        req = CandidateTokenRequest(email="demo.candidate@example.com")
        resp = await request_candidate_token(req)
        print(f"   Response: {resp}")
        
        if resp.token == "demo-token-bypass":
             print("   PASS: Bypass token received.")
        else:
             print("   FAIL: Did not receive bypass token.")
             return
    except Exception as e:
        print(f"   FAIL: Exception {e}")
        import traceback
        traceback.print_exc()

    # 2. Test Login with bypass token
    print("\n2. Logging in with 'demo-token-bypass'...")
    try:
        # We assume cand_xyz exists or the bypass handles fallback
        req_login = CandidateLoginRequest(candidate_id="cand_xyz", token="demo-token-bypass")
        resp_login = await candidate_login(req_login)
        print(f"   Response: {resp_login}")
        print("   PASS: Login successful via bypass.")

    except Exception as e:
        print(f"   FAIL: Exception {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(verify_bypass())
