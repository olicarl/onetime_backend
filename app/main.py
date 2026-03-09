from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from starlette.middleware.cors import CORSMiddleware
from app.config import logger
from app.gateway.connection_manager import manager
from app.gateway.handlers.ocpp_handler import ChargePoint
from app.services.transactions import transaction_service # Import to register event listeners
from app.middleware.auth import DualModeAuthMiddleware
from app.routers import auth, admin

app = FastAPI(title="Onetime Backend", version="2.0.0")

@app.get("/health")
async def health_check():
    return {"status": "ok"}

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # For dev, restrict in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(DualModeAuthMiddleware)

@app.on_event("startup")
async def startup():
    logger.info("Starting Onetime Backend (Monolith)...")
    logger.info("Event listeners registered via imports.")
    
    from app.services.watchdog import watchdog
    watchdog.start()

# Routes
app.include_router(auth.router)
app.include_router(admin.router)

class SocketAdapter:
    def __init__(self, websocket: WebSocket):
        self._ws = websocket

    async def recv(self):
        return await self._ws.receive_text()

    async def send(self, msg):
        await self._ws.send_text(msg)

import asyncio

@app.websocket("/ocpp/{charge_point_id}")
async def on_connect(websocket: WebSocket, charge_point_id: str):
    await manager.connect(charge_point_id, websocket)
    
    cp = ChargePoint(charge_point_id, SocketAdapter(websocket))
    
    # Store the ChargePoint instance on the WebSocket object 
    # so we can retrieve it for outgoing commands (Rule C implementation)
    websocket.charge_point = cp
    
    # Trigger a StatusNotification shortly after connection
    async def trigger_status():
        await asyncio.sleep(2) # Give it a moment to stabilize
        try:
            if await station_service.has_unknown_connector_status(charge_point_id):
                logger.info(f"Unknown status detected. Triggering StatusNotification for {charge_point_id} on reconnect.")
                await cp.trigger_message(requested_message="StatusNotification")
            else:
                logger.info(f"Status already known for {charge_point_id}. Skipping StatusNotification trigger.")
        except Exception as e:
            logger.error(f"Failed to trigger StatusNotification for {charge_point_id}: {e}")
            
    asyncio.create_task(trigger_status())
    
    try:
        await cp.start()
    except WebSocketDisconnect:
        await manager.disconnect(charge_point_id)
    except Exception as e:
        logger.error(f"Error in OCPP connection: {e}")
        await manager.disconnect(charge_point_id)
