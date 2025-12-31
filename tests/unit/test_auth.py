from fastapi import status

def test_login_success(client, db_session, test_user):
    # Depending on how your auth service checks passwords, we might need to mock verify_password
    # or ensure "hashed_password" matches what verify_password expects for a given input.
    # However, for unit testing the router, we often mock the service layer.
    
    # Real integration test with actual password hashing:
    # We would need to generate a real hash for the test user.
    # For now, let's assume the user service works as expected or mock it.
    
    # Let's mock the user_service.authenticate_user to avoid hashing complexity here
    from app.services.user_service import user_service
    from unittest.mock import MagicMock
    
    # Save original method
    original_auth = user_service.authenticate_user
    
    # Mock
    user_service.authenticate_user = MagicMock(return_value=test_user)
    
    response = client.post("/api/login", json={"username": "testadmin", "password": "password"})
    
    # Restore
    user_service.authenticate_user = original_auth
    
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"message": "Login successful"}
    assert "access_token" in response.cookies

def test_login_failure(client):
    from app.services.user_service import user_service
    from unittest.mock import MagicMock
    
    original_auth = user_service.authenticate_user
    user_service.authenticate_user = MagicMock(return_value=None)
    
    response = client.post("/api/login", json={"username": "wrong", "password": "wrong"})
    
    user_service.authenticate_user = original_auth
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {"detail": "Invalid credentials"}

def test_get_me_authenticated(client, auth_headers):
    # Need to override the dependency that extracts user from token/cookie
    # Or just rely on the fact that we have a valid token in cookie
    
    # However, DualModeAuthMiddleware populates request.state.user
    # We need to make sure the middleware runs or the dependency that reads it works.
    
    # The 'get_current_user' in auth.py reads request.state.user
    # The DualModeAuthMiddleware decodes the token and sets request.state.user
    
    # We need to ensure that the token generated in conftest.py is valid for the app's secret key.
    # Since we import create_access_token from app.security, it uses the same key.
    
    response = client.get("/api/me", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["username"] == "testadmin"
    assert data["role"] == "admin"

def test_get_me_unauthenticated(client):
    response = client.get("/api/me")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

def test_logout(client):
    response = client.post("/api/logout")
    assert response.status_code == status.HTTP_200_OK
    assert "access_token" not in response.cookies or response.cookies["access_token"] == ""

