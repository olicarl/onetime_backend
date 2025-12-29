from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from app.config import logger
from app.security import decode_access_token
from app.services.user_service import user_service
import os

# CONFIG
TRUST_PROXY_HEADERS = os.getenv("TRUST_PROXY_HEADERS", "False").lower() == "true"
PROXY_USER_HEADER = os.getenv("PROXY_USER_HEADER", "X-Forwarded-User")

class DualModeAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # 1. Check for Trusted Proxy Headers (Cloud Mode)
        if TRUST_PROXY_HEADERS:
            proxy_user = request.headers.get(PROXY_USER_HEADER)
            if proxy_user:
                # In a real app, you might sync this user to DB or just trust the header
                # For now, we'll create a transient state object
                request.state.user = {"username": proxy_user, "role": "admin", "mode": "cloud"}
                return await call_next(request)

        # 2. Check for Session Cookie (Local Mode)
        token = request.cookies.get("access_token")
        if token:
            payload = decode_access_token(token)
            if payload:
                username = payload.get("sub")
                if username:
                    # User authenticated via local login
                    request.state.user = {"username": username, "role": "admin", "mode": "local"}
                    return await call_next(request)

        # 3. No Auth - Set state to None (Endpoints can decide to enforce or not)
        request.state.user = None
        
        return await call_next(request)
