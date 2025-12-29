import asyncio
from app.config import logger
from app.gateway.connection_manager import manager
from app.services.station_service import station_service

class StationWatchdog:
    def __init__(self, interval_seconds: int = 60):
        self.interval = interval_seconds
        self.running = False
        self._task = None

    def start(self):
        if not self.running:
            self.running = True
            self._task = asyncio.create_task(self._loop())
            logger.info("StationWatchdog: Started.")

    async def stop(self):
        self.running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            logger.info("StationWatchdog: Stopped.")

    async def _loop(self):
        # Initial cleanup on startup
        logger.info("StationWatchdog: Performing startup cleanup...")
        await self._sync()
        
        while self.running:
            try:
                await asyncio.sleep(self.interval)
                await self._sync()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"StationWatchdog error: {e}")

    async def _sync(self):
        # Get list of currently connected charger IDs from memory
        active_ids = list(manager.active_connections.keys())
        # Call service to update DB
        await station_service.sync_active_stations(active_ids)

watchdog = StationWatchdog(interval_seconds=60)
