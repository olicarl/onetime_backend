"""
Relay Agent Service - Manages the integrated relay agent
"""
import asyncio
import logging
from typing import Optional
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import RelaySettings
from .client import RelayClient

logger = logging.getLogger("relay_agent")


class RelayAgentService:
    """Service to manage relay agent lifecycle"""
    
    _instance: Optional["RelayAgentService"] = None
    _client: Optional[RelayClient] = None
    _task: Optional[asyncio.Task] = None
    
    DEFAULT_RELAY_URL = "wss://relay.onetimerelay.com/ws/connect"
    
    @classmethod
    def get_instance(cls) -> "RelayAgentService":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    async def start(self):
        """Start the relay agent if enabled"""
        db = SessionLocal()
        try:
            settings = db.query(RelaySettings).first()
            
            if not settings:
                logger.info("No relay settings found, agent not starting")
                return
            
            if not settings.enabled:
                logger.info("Relay agent disabled")
                return
            
            if not settings.encrypted_token:
                logger.warning("Relay agent enabled but no token configured")
                return
            
            token = settings.get_token()
            relay_url = settings.relay_url or self.DEFAULT_RELAY_URL
            
            self._client = RelayClient(
                relay_url=relay_url,
                token=token,
                local_backend_url="http://localhost:8000"
            )
            
            self._task = asyncio.create_task(self._client.run())
            logger.info(f"Relay agent started, connecting to {relay_url}")
            
        except Exception as e:
            logger.error(f"Failed to start relay agent: {e}")
        finally:
            db.close()
    
    async def stop(self):
        """Stop the relay agent"""
        if self._client:
            await self._client.stop()
            self._client = None
        
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        
        logger.info("Relay agent stopped")
    
    async def restart(self):
        """Restart the relay agent"""
        await self.stop()
        await asyncio.sleep(1)
        await self.start()
    
    def get_status(self) -> dict:
        """Get agent status"""
        if self._client:
            return self._client.get_status()
        return {
            "connected": False,
            "running": False,
            "message": "Agent not running"
        }
