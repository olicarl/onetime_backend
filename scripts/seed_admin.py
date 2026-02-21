import sys
import os

# Add parent directory to path so we can import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from app.services.user_service import user_service
from app.config import logger

def seed_admin():
    db = SessionLocal()
    try:
        if not user_service.get_user_by_username("admin"):
            logger.info("Seeding admin user...")
            user_service.create_user("admin", "admin", "admin")
            logger.info("Admin user 'admin' created with password 'admin'.")
        else:
            logger.info("Admin user already exists.")
    except Exception as e:
        logger.error(f"Error seeding admin: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_admin()
