from sqlalchemy.orm import Session
from app.models import User
from app.security import get_password_hash, verify_password
from app.database import SessionLocal
from typing import Optional

class UserService:
    def get_user_by_username(self, username: str) -> Optional[User]:
        db: Session = SessionLocal()
        try:
            return db.query(User).filter(User.username == username).first()
        finally:
            db.close()

    def create_user(self, username: str, password: str, role: str = "admin") -> User:
        db: Session = SessionLocal()
        try:
            hashed_password = get_password_hash(password)
            db_user = User(username=username, password_hash=hashed_password, role=role)
            db.add(db_user)
            db.commit()
            db.refresh(db_user)
            return db_user
        finally:
            db.close()

    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        user = self.get_user_by_username(username)
        if not user:
            return None
        if not verify_password(password, user.password_hash):
            return None
        return user

user_service = UserService()
