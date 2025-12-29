import asyncio
import websockets
import logging
from app.database import SessionLocal
from app.models import ChargingStation
from app.config import logger as app_logger

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_status")

async def test_connection_status():
    station_id = "CP_STATUS_TEST"
    server_url = f"ws://localhost:8000/ocpp/{station_id}"
    
    logger.info(f"Connecting to {server_url}...")
    
    try:
        async with websockets.connect(server_url, subprotocols=["ocpp1.6"]) as ws:
            logger.info("Connected.")
            await asyncio.sleep(1) # Wait for connect logic
            
            # Send StatusNotification to set connector 1 to Available
            # [MessageTypeId, UniqueId, Action, Payload]
            # 2 = Call
            msg_id = "123456"
            msg = [
                2, 
                msg_id, 
                "StatusNotification", 
                {
                    "connectorId": 1,
                    "errorCode": "NoError",
                    "status": "Available"
                }
            ]
            import json
            await ws.send(json.dumps(msg))
            logger.info("Sent StatusNotification (Available)")
            
            # Wait for response
            resp = await ws.recv()
            logger.info(f"Received: {resp}")
            
            await asyncio.sleep(2) # Give it time to update DB
            
            # Check DB - Should be ONLINE and Connector AVAILABLE
            db = SessionLocal()
            station = db.query(ChargingStation).filter(ChargingStation.id == station_id).first()
            if not station or not station.is_online:
                logger.error("FAILURE: Station should be ONLINE")
                raise Exception("Station should be ONLINE")
            
            from app.models import StationConnector, ChargingStationStatus
            connector = db.query(StationConnector).filter(
                StationConnector.station_id == station_id,
                StationConnector.connector_id == 1
            ).first()
            
            if not connector or connector.status != ChargingStationStatus.Available:
                 logger.error(f"FAILURE: Connector status is {connector.status if connector else 'None'}, expected Available")
                 raise Exception("Connector should be Available")
            
            logger.info("SUCCESS: Station ONLINE, Connector AVAILABLE")
            db.close()
            
            # Disconnect happens when we exit the block
        
        logger.info("Disconnected.")
        await asyncio.sleep(2) # Give it time to update DB logic (disconnect + watchdog if applicable, though disconnect is immediate)
        
        # Check DB - Should be OFFLINE and Connector UNKNOWN
        db = SessionLocal()
        station = db.query(ChargingStation).filter(ChargingStation.id == station_id).first()
        if station and not station.is_online:
             logger.info("SUCCESS: Station is OFFLINE in DB")
        else:
            logger.error(f"FAILURE: Station is ONLINE in DB. Status: {station.is_online if station else 'Not Found'}")
            raise Exception("Station should be OFFLINE")
            
        connector = db.query(StationConnector).filter(
                StationConnector.station_id == station_id,
                StationConnector.connector_id == 1
            ).first()
            
        if not connector or connector.status != ChargingStationStatus.Unknown:
             logger.error(f"FAILURE: Connector status is {connector.status if connector else 'None'}, expected Unknown")
             raise Exception("Connector should be Unknown")
             
        logger.info("SUCCESS: Station OFFLINE, Connector UNKNOWN")
        db.close()

    except Exception as e:
        logger.error(f"Test Failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(test_connection_status())
