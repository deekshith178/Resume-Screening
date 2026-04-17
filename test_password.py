from backend.security import verify_password, get_password_hash
from backend.database import get_session
from backend.models import Recruiter
from sqlalchemy import select

# Get the user from database
with get_session() as db:
    user = db.execute(select(Recruiter).where(Recruiter.email == 'test@example.com')).scalars().first()
    
    if user:
        print(f"User found: {user.email}")
        print(f"Role: {user.role}")
        print(f"Stored hash: {user.hashed_password[:60]}...")
        print()
        
        # Test password verification
        test_password = "password123"
        print(f"Testing password: '{test_password}'")
        
        result = verify_password(test_password, user.hashed_password)
        print(f"Verification result: {result}")
        
        if not result:
            print("\nPassword verification FAILED!")
            print("Let's create a new hash and compare:")
            new_hash = get_password_hash(test_password)
            print(f"New hash: {new_hash[:60]}...")
            print(f"Stored hash: {user.hashed_password[:60]}...")
        else:
            print("\nPassword verification SUCCESS!")
    else:
        print("User not found!")
