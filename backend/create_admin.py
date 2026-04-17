
from .database import get_session
from .models import Recruiter
from .security import get_password_hash
from sqlalchemy import select

def create_admin():
    print("Checking for admin user...")
    with get_session() as db:
        # Check if exists
        existing = db.execute(select(Recruiter).where(Recruiter.email == "test@example.com")).scalars().first()
        if existing:
            print("Admin user 'test@example.com' already exists.")
            return

        print("Creating admin user...")
        admin = Recruiter(
            email="test@example.com",
            hashed_password=get_password_hash("password123"),
            role="admin"
        )
        db.add(admin)
        print("Admin user created: test@example.com / password123")

if __name__ == "__main__":
    create_admin()
