import os
import sys

sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
)

from app.auth.hashing import hash_password
from app.auth.roles import ADMIN
from app.db.session import SessionLocal
from app.models.user import User

ADMIN_EMAIL = "admin@school.com"
ADMIN_PASSWORD = "ChangeMe123!"


def create_admin() -> None:
    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.email == ADMIN_EMAIL).first()
        if existing:
            print("Admin already exists.")
            return

        admin = User(
            email=ADMIN_EMAIL,
            hashed_password=hash_password(ADMIN_PASSWORD),
            role=ADMIN,
            is_active=True,
            must_change_password=True,
        )
        db.add(admin)
        db.commit()
        print("Admin account created successfully.")
        print(f"  Email: {ADMIN_EMAIL}")
        print(f"  Password: {ADMIN_PASSWORD} (change on first login)")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    create_admin()
