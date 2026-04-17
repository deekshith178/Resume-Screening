from backend.security import verify_recruiter_credentials

# Test the verify_recruiter_credentials function directly
username = "test@example.com"
password = "password123"

print(f"Testing verify_recruiter_credentials('{username}', '{password}')")
result = verify_recruiter_credentials(username, password)
print(f"Result: {result}")

if result:
    print("\nCredentials verification SUCCESS!")
else:
    print("\nCredentials verification FAILED!")
    print("This function should return True but it's returning False")
