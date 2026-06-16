from app.auth.security import hash_password
from app.database.db import SessionLocal
from app.models.user import User, UserRole


ADMIN_EMAIL = "admin@system.com"
ADMIN_PASSWORD = "Admin@123"


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
            is_active=True
        )

        db.add(admin)
        db.commit()

        print("Admin created")

    finally:
        db.close()


if __name__ == "__main__":
    seed_admin()
