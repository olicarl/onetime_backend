from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from starlette.middleware.cors import CORSMiddleware
from app.config import logger
from app.gateway.connection_manager import manager
from app.gateway.handlers.ocpp_handler import ChargePoint
from app.services.transactions import transaction_service # Import to register event listeners
from app.middleware.auth import DualModeAuthMiddleware
from app.routers import auth, admin

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.orm import Session
from datetime import datetime, timezone
import asyncio

from app.database import SessionLocal
from app.models import Renter, BillingPeriodicity
from app.services.billing_service import get_billing_settings, calculate_and_generate_invoice
from app.services.station_service import station_service

app = FastAPI(title="Onetime Backend", version="2.0.0")

scheduler = AsyncIOScheduler()

async def auto_billing_job():
    logger.info("Running automatic billing background job...")
    db: Session = SessionLocal()
    try:
        settings = get_billing_settings(db)
        today = datetime.now(timezone.utc)
        
        # Check if today is the end of a period
        is_end_of_period = False
        
        if settings.periodicity == BillingPeriodicity.Monthly and today.day == 1:
            is_end_of_period = True
        elif settings.periodicity == BillingPeriodicity.Quarterly and today.month in [1, 4, 7, 10] and today.day == 1:
            is_end_of_period = True
        elif settings.periodicity == BillingPeriodicity.HalfYearly and today.month in [1, 7] and today.day == 1:
            is_end_of_period = True
        elif settings.periodicity == BillingPeriodicity.Yearly and today.month == 1 and today.day == 1:
            is_end_of_period = True
            
        if is_end_of_period:
            renters = db.query(Renter).filter(Renter.is_active == True).all()
            for renter in renters:
                try:
                    invoice = calculate_and_generate_invoice(db, renter, today)
                    if invoice:
                        logger.info(f"Automatically generated invoice {invoice.id} for renter {renter.name}")
                except Exception as e:
                    logger.error(f"Failed to generate automatic invoice for renter {renter.name}: {e}")
        else:
            logger.info("Today is not the end of a configured billing period. No invoices generated.")
    except Exception as e:
        logger.error(f"Error in automatic billing job: {e}")
    finally:
        db.close()

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
    
    # Schedule the auto_billing_job to run every day at 00:01
    scheduler.add_job(auto_billing_job, CronTrigger(hour=0, minute=1))
    scheduler.start()
    logger.info("APScheduler started.")

# Routes
app.include_router(auth.router)
app.include_router(admin.router)
from app.routers import billing
app.include_router(billing.router)

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
