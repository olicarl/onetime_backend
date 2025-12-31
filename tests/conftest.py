import os
# Set DB URL for tests to localhost:5433 (host port for db)
# We must do this before importing app.config or app.database
os.environ["DATABASE_URL"] = "postgresql://user:password@localhost:5433/onetime"

import pytest
from starlette.testclient import TestClient
from app.main import app
from app.database import SessionLocal, engine, Base
from app.services.user_service import user_service
from app.security import create_access_token
from app.models import User

@pytest.fixture(scope="session")
def db_engine():
    # You might want to create a test database here
    # For now, we use the existing engine, but in a real scenario
    # we would use a separate test DB.
    yield engine

@pytest.fixture(scope="function")
def db_session(db_engine):
    connection = db_engine.connect()
    transaction = connection.begin()
    session = SessionLocal(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture(scope="function")
def client(db_session):
    # Override the get_db dependency
    from app.routers.admin import get_db
    app.dependency_overrides[get_db] = lambda: db_session
    
    with TestClient(app) as c:
        yield c
    
    app.dependency_overrides.clear()

@pytest.fixture(scope="function")
def test_user(db_session):
    # Create a test user if not exists
    user = db_session.query(User).filter(User.username == "testadmin").first()
    if not user:
        user = User(username="testadmin", password_hash="hashed_password", role="admin")
        db_session.add(user)
        db_session.commit()
    return user

@pytest.fixture(scope="function")
def admin_token(test_user):
    return create_access_token(data={"sub": test_user.username, "role": "admin"})

@pytest.fixture(scope="function")
def auth_headers(admin_token):
    return {"Cookie": f"access_token={admin_token}"}
