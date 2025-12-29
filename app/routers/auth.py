from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from pydantic import BaseModel
from typing import Optional
from app.services.user_service import user_service
from app.security import create_access_token

router = APIRouter(prefix="/api", tags=["Auth"])

class LoginRequest(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    username: str
    role: str
    mode: str

@router.post("/login")
async def login(response: Response, creds: LoginRequest):
    user = user_service.authenticate_user(creds.username, creds.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    
    # Create Session Cookie
    access_token = create_access_token(data={"sub": user.username, "role": user.role})
    
    # HttpOnly Cookie for security
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=60 * 60 * 24, # 1 day
        samesite="lax",
        secure=False  # Set to True in production (HTTPS)
    )
    
    return {"message": "Login successful"}

@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie("access_token")
    return {"message": "Logged out"}

@router.get("/me", response_model=UserResponse)
async def get_current_user(request: Request):
    user = request.state.user
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return user
