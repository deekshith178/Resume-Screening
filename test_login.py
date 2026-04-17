# Direct test of the actual login endpoint with detailed debugging
import requests
import json

url = "http://localhost:8001/auth/recruiter/login"
payload = {"username": "test@example.com", "password": "password123"}

print("=" * 60)
print("TESTING BACKEND LOGIN ENDPOINT")
print("=" * 60)
print(f"URL: {url}")
print(f"Payload: {json.dumps(payload, indent=2)}")
print()

try:
    response = requests.post(url, json=payload, timeout=5)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code == 200:
        print("\n" + "=" * 60)
        print("SUCCESS! Login worked!")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("FAILED! Check backend logs above")
        print("=" * 60)
except requests.exceptions.ConnectionError:
    print("\nERROR: Cannot connect to backend. Is it running on port 8000?")
except Exception as e:
    print(f"\nERROR: {e}")
