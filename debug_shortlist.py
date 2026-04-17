"""Test shortlist endpoint to debug candidate loading."""
import requests

BASE_URL = "http://localhost:8000"

# First, login as recruiter
login_resp = requests.post(f"{BASE_URL}/auth/recruiter/login", json={
    "username": "newrecruiter2@test.com",
    "password": "TestPass123!"
})

if login_resp.status_code != 200:
    print(f"Login failed: {login_resp.status_code}")
    print(login_resp.text)
    exit(1)

token = login_resp.json().get("access_token")
print(f"Login successful, token obtained")

# Get jobs list
jobs_resp = requests.get(f"{BASE_URL}/jobs", headers={
    "Authorization": f"Bearer {token}"
})

if jobs_resp.status_code != 200:
    print(f"Get jobs failed: {jobs_resp.status_code}")
    print(jobs_resp.text)
    exit(1)

jobs = jobs_resp.json().get("items", [])
print(f"Found {len(jobs)} jobs")

if not jobs:
    print("No jobs found")
    exit(1)

job_id = "job-advocate"
print(f"Testing shortlist for job: {job_id}")

# Get shortlist
shortlist_resp = requests.get(
    f"{BASE_URL}/jobs/{job_id}/shortlist",
    headers={"Authorization": f"Bearer {token}"}
)

print(f"Shortlist response status: {shortlist_resp.status_code}")
if shortlist_resp.status_code != 200:
    print(f"Shortlist failed: {shortlist_resp.text}")
else:
    data = shortlist_resp.json()
    print(f"Candidates returned: {len(data.get('candidates', []))}")
    if data.get('candidates'):
        c = data['candidates'][0]
        print(f"First candidate: {c.get('name')} - Score: {c.get('score')}")
        print(f"Components: {c.get('components')}")
