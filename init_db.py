import os

from app.core.database import SessionLocal, init_database
from app.core.security import get_password_hash
from app.models.models import User, UserRole
from app.services.selection import get_or_create_settings


def main() -> None:
    init_database()
    db = SessionLocal()
    try:
        get_or_create_settings(db)
        admin_username = os.getenv("ADMIN_USERNAME", "admin")
        admin_password = os.getenv("ADMIN_PASSWORD", "admin123456")
        admin_name = os.getenv("ADMIN_FULL_NAME", "System Admin")

        admin = db.query(User).filter(User.username == admin_username).first()
        if not admin:
            admin = User(
                username=admin_username,
                full_name=admin_name,
                role=UserRole.admin,
                hashed_password=get_password_hash(admin_password),
                is_active=True,
            )
            db.add(admin)
            db.commit()
            print(f"Created default admin: {admin_username}")
        else:
            print(f"Admin already exists: {admin_username}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
