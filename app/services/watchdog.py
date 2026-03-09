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
                
                # After syncing DB, check if any active connections are stuck in Unknown status
                active_ids = list(manager.active_connections.keys())
                await self._poll_unknown_statuses(active_ids)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"StationWatchdog error: {e}")

    async def _sync(self):
        # Get list of currently connected charger IDs from memory
        active_ids = list(manager.active_connections.keys())
        # Call service to update DB
        await station_service.sync_active_stations(active_ids)

    async def _poll_unknown_statuses(self, active_ids: list[str]):
        if not active_ids:
            return
            
        for charger_id in active_ids:
            try:
                # Check DB if status is still unknown
                if await station_service.has_unknown_connector_status(charger_id):
                    logger.info(f"Watchdog: Connector status for {charger_id} is still Unknown. Sending TriggerMessage.")
                    
                    # Fetch websocket connection
                    websocket = manager.get_connection(charger_id)
                    if websocket and hasattr(websocket, 'charge_point'):
                        cp = websocket.charge_point
                        # Fire and forget the trigger message
                        asyncio.create_task(
                            cp.trigger_message(requested_message="StatusNotification")
                        )
            except Exception as e:
                logger.error(f"Watchdog error while polling status for {charger_id}: {e}")

watchdog = StationWatchdog(interval_seconds=60)
