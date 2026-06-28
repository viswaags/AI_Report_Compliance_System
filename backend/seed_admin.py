from app.auth.security import hash_password
from app.database.db import SessionLocal
from app.models.user import User, UserRole
import os

from dotenv import load_dotenv

load_dotenv()

ADMIN_EMAIL = os.getenv("ADMIN_EMAIL")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")


def seed_admin() -> None:
    db = SessionLocal()

    try:
        existing_admin = db.query(User).filter(User.email == ADMIN_EMAIL).first()

        if existing_admin:
            print("Admin already exists")
            return

        admin = User(
            name="Admin",
            email=ADMIN_EMAIL,
            password_hash=hash_password(ADMIN_PASSWORD),
            role=UserRole.ADMIN,
            is_active=True,
            created_by=None
        )

        db.add(admin)
        db.commit()

        print("Admin created")

    finally:
        db.close()


if __name__ == "__main__":
    seed_admin()
