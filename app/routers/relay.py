"""
Relay Management Router - API for managing relay connection
"""
import os
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.middleware.auth import get_current_user
from app.models import User, RelaySettings
from app.relay_agent.service import RelayAgentService

router = APIRouter(prefix="/api/relay", tags=["relay"])


class RelaySettingsInput(BaseModel):
    enabled: bool = False
    token: Optional[str] = None
    relay_url: Optional[str] = None


class RelaySettingsResponse(BaseModel):
    enabled: bool
    connected: bool
    relay_url: str
    last_error: Optional[str] = None
    connected_at: Optional[str] = None


class RelayStatusResponse(BaseModel):
    enabled: bool
    connected: bool
    running: bool
    relay_url: Optional[str] = None
    connected_at: Optional[str] = None
    last_error: Optional[str] = None


DEFAULT_RELAY_URL = os.getenv("RELAY_URL", "wss://relay.onetimerelay.com/ws/connect")


@router.get("/settings", response_model=RelaySettingsResponse)
async def get_relay_settings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    settings = db.query(RelaySettings).first()
    service = RelayAgentService.get_instance()
    status_info = service.get_status()
    
    if not settings:
        return RelaySettingsResponse(
            enabled=False,
            connected=status_info.get("connected", False),
            relay_url=DEFAULT_RELAY_URL,
            last_error=None,
            connected_at=None
        )
    
    return RelaySettingsResponse(
        enabled=settings.enabled,
        connected=status_info.get("connected", False),
        relay_url=settings.relay_url or DEFAULT_RELAY_URL,
        last_error=status_info.get("last_error"),
        connected_at=status_info.get("connected_at")
    )


@router.post("/settings", response_model=RelaySettingsResponse)
async def update_relay_settings(
    settings_input: RelaySettingsInput,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    settings = db.query(RelaySettings).first()
    if not settings:
        settings = RelaySettings()
        db.add(settings)
    
    settings.enabled = settings_input.enabled
    
    if settings_input.token:
        settings.set_token(settings_input.token)
    
    if settings_input.relay_url:
        settings.relay_url = settings_input.relay_url
    elif not settings.relay_url:
        settings.relay_url = DEFAULT_RELAY_URL
    
    db.commit()
    
    service = RelayAgentService.get_instance()
    await service.restart()
    
    status_info = service.get_status()
    
    return RelaySettingsResponse(
        enabled=settings.enabled,
        connected=status_info.get("connected", False),
        relay_url=settings.relay_url,
        last_error=status_info.get("last_error"),
        connected_at=status_info.get("connected_at")
    )


@router.get("/status", response_model=RelayStatusResponse)
async def get_relay_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    settings = db.query(RelaySettings).first()
    service = RelayAgentService.get_instance()
    status_info = service.get_status()
    
    return RelayStatusResponse(
        enabled=settings.enabled if settings else False,
        connected=status_info.get("connected", False),
        running=status_info.get("running", False),
        relay_url=settings.relay_url if settings else DEFAULT_RELAY_URL,
        connected_at=status_info.get("connected_at"),
        last_error=status_info.get("last_error")
    )


@router.post("/restart")
async def restart_relay_agent(
    current_user: User = Depends(get_current_user)
):
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    service = RelayAgentService.get_instance()
    await service.restart()
    
    return {"message": "Relay agent restarted", "status": service.get_status()}
