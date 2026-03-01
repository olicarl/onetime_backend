import asyncio
import logging

logging.basicConfig(level=logging.DEBUG)

from app.database import SessionLocal
from app.models import ChargingStation
from app.services.transactions import transaction_service

async def main():
    print("Testing Kiosk Mode Enabled...")
    db = SessionLocal()
    try:
        print("Connected to DB")
        charger1 = ChargingStation(id='cp001_kiosk', kiosk_mode=True)
        db.merge(charger1)
        db.commit()
        print("Committed charger")
    finally:
        db.close()
    
    print("Running start_transaction")
    res1 = await transaction_service.start_transaction('cp001_kiosk', 1, 'UNKNOWN_TAG_001', 0, '2026-03-01T20:00:00Z')
    print("Result (Kiosk Enabled):", res1)

if __name__ == "__main__":
    print("Starting")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Interrupted")
    print("Done")
