from datetime import datetime
from sqlalchemy.orm import Session
from app.database import get_db, SessionLocal
from app.models import ChargingStation, BootLog, StationConnector, ChargingStationStatus
from app.config import logger

class StationService:
    
    async def process_boot(self, charger_id: str, vendor: str, model: str, firmware_version: str = None, **kwargs):
        """
        Handle BootNotification:
        1. Log the boot attempt.
        2. Update/Create the ChargingStation record.
        3. Return Accepted if known/auto-accept.
        """
        db: Session = SessionLocal()
        try:
            # 1. Log Boot
            boot_log = BootLog(
                station_id=charger_id,
                model=model,
                vendor=vendor,
                firmware_version=firmware_version
            )
            # We need to ensure station exists first or this might fail depending on FK constraints
            # So check station first
            
            station = db.query(ChargingStation).filter(ChargingStation.id == charger_id).first()
            if not station:
                # Auto-create for this simplified backend
                station = ChargingStation(
                    id=charger_id,
                    is_online=True,
                    model=model,
                    vendor=vendor,
                    firmware_version=firmware_version
                )
                db.add(station)
                logger.info(f"Created new station: {charger_id}")
            else:
                station.is_online = True
                station.model = model
                station.vendor = vendor
                station.firmware_version = firmware_version
            
            db.commit() # Commit station first

            db.add(boot_log)
            db.commit()

            return {
                "status": "Accepted",
                "interval": 300,
                "current_time": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Error processing boot for {charger_id}: {e}")
            return {"status": "Rejected", "interval": 0}
        finally:
            db.close()

    async def heartbeat(self, charger_id: str, **kwargs):
        db: Session = SessionLocal()
        try:
            station = db.query(ChargingStation).filter(ChargingStation.id == charger_id).first()
            if station:
                station.last_heartbeat = datetime.utcnow()
                station.is_online = True
                db.commit()
            
            return {"current_time": datetime.utcnow().isoformat()}
        finally:
            db.close()

    async def handle_status_notification(self, charger_id: str, connector_id: int, status: str, error_code: str, **kwargs):
        db: Session = SessionLocal()
        try:
            # Upsert Connector
            connector = db.query(StationConnector).filter(
                StationConnector.station_id == charger_id,
                StationConnector.connector_id == connector_id
            ).first()

            if not connector:
                connector = StationConnector(
                    station_id=charger_id,
                    connector_id=connector_id
                )
                db.add(connector)
            
            connector.status = status
            connector.error_code = error_code
            connector.last_updated = datetime.utcnow()
            
            db.commit()
        except Exception as e:
            logger.error(f"Error updating status for {charger_id}:{connector_id}: {e}")
        finally:
            db.close()

station_service = StationService()
