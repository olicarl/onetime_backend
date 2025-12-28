import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from app.config import logger
from app.gateway.connection_manager import manager
from app.gateway.handlers.ocpp_handler import ChargePoint
from app.services.transactions import transaction_service # Import to register event listeners

app = FastAPI(title="Onetime Backend", version="2.0.0")

@app.on_event("startup")
async def startup():
    logger.info("Starting Onetime Backend (Monolith)...")
    logger.info("Event listeners registered via imports.")

# Include Dashboard
from app.gateway.routers import web
app.include_router(web.router)

@app.websocket("/ocpp/{charge_point_id}")
async def on_connect(websocket: WebSocket, charge_point_id: str):
    await manager.connect(charge_point_id, websocket)
    
    cp = ChargePoint(charge_point_id, websocket)
    
    # Store the ChargePoint instance on the WebSocket object 
    # so we can retrieve it for outgoing commands (Rule C implementation)
    websocket.charge_point = cp
    
    try:
        await cp.start()
    except WebSocketDisconnect:
        manager.disconnect(charge_point_id)
    except Exception as e:
        logger.error(f"Error in OCPP connection: {e}")
        manager.disconnect(charge_point_id)
