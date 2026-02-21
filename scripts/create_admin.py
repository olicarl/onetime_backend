#!/usr/bin/env python3
"""
Script to create an admin user in the database.
Usage: python create_admin.py [username] [password]
Default: admin / admin
"""

import sys
import os

# Add parent directory to path so we can import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import bcrypt

# Database connection - use environment variable or default
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5433/onetime")

def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def create_admin_user(username: str = "admin", password: str = "admin"):
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    db = SessionLocal()
    
    try:
        # Check if user already exists
        from app.models import User
        existing_user = db.query(User).filter(User.username == username).first()
        
        if existing_user:
            print(f"User '{username}' already exists. Updating password...")
            existing_user.password_hash = get_password_hash(password)
            db.commit()
            print(f"✅ Password updated for user '{username}'")
        else:
            # Create new user
            new_user = User(
                username=username,
                password_hash=get_password_hash(password),
                role="admin",
                is_active=True
            )
            db.add(new_user)
            db.commit()
            print(f"✅ Admin user '{username}' created successfully!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    username = sys.argv[1] if len(sys.argv) > 1 else "admin"
    password = sys.argv[2] if len(sys.argv) > 2 else "admin"
    
    print(f"Creating admin user: {username}")
    create_admin_user(username, password)
