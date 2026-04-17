# Create a completely fresh test to bypass any caching
import requests
import json
from datetime import datetime

url = "http://localhost:8000/auth/recruiter/login"
payload = {"username": "test@example.com", "password": "password123"}

print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Sending login request...")
print(f"URL: {url}")
print(f"Payload: {json.dumps(payload)}")

try:
    response = requests.post(url, json=payload, timeout=10)
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Response received")
    print(f"Status: {response.status_code}")
    print(f"Body: {response.text}")
    
    if response.status_code == 200:
        print("\n[OK] LOGIN SUCCESSFUL")
        data = response.json()
        print(f"Token: {data.get('access_token', 'N/A')[:50]}...")
    else:
        print("\n[FAIL] LOGIN FAILED")
        print("Check the backend terminal for debug logs")
        
except Exception as e:
    print(f"\n[ERROR] {e}")
