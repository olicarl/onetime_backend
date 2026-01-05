from typing import Dict
from fastapi import WebSocket
from app.config import logger

from app.services.station_service import station_service

class ConnectionRegistry:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConnectionRegistry, cls).__new__(cls)
            cls._instance.active_connections: Dict[str, WebSocket] = {}
        return cls._instance

    async def connect(self, charger_id: str, websocket: WebSocket):
        await websocket.accept(subprotocol='ocpp1.6')
        self.active_connections[charger_id] = websocket
        logger.info(f"Charger {charger_id} connected. Total: {len(self.active_connections)}")
        await station_service.set_station_online(charger_id)

    async def disconnect(self, charger_id: str):
        if charger_id in self.active_connections:
            del self.active_connections[charger_id]
            logger.info(f"Charger {charger_id} disconnected. Total: {len(self.active_connections)}")
        await station_service.set_station_offline(charger_id)

    def get_connection(self, charger_id: str) -> WebSocket:
        return self.active_connections.get(charger_id)

manager = ConnectionRegistry()
