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

    async def set_station_online(self, charger_id: str):
        db: Session = SessionLocal()
        try:
            station = db.query(ChargingStation).filter(ChargingStation.id == charger_id).first()
            if not station:
                logger.info(f"Station {charger_id} connected but not found in DB. Creating placeholder.")
                station = ChargingStation(id=charger_id, is_online=True)
                db.add(station)
            else:
                station.is_online = True
            db.commit()
            logger.info(f"Station {charger_id} marked as ONLINE")
        except Exception as e:
            logger.error(f"Error marking station {charger_id} online: {e}")
        finally:
            db.close()

    async def set_station_offline(self, charger_id: str):
        db: Session = SessionLocal()
        try:
            station = db.query(ChargingStation).filter(ChargingStation.id == charger_id).first()
            if station:
                station.is_online = False
                
                # Update connectors to Unknown
                db.query(StationConnector).filter(
                    StationConnector.station_id == charger_id
                ).update(
                    {StationConnector.status: ChargingStationStatus.Unknown}, 
                    synchronize_session=False
                )
                
                db.commit()
                logger.info(f"Station {charger_id} marked as OFFLINE (Connectors: Unknown)")
        except Exception as e:
            logger.error(f"Error marking station {charger_id} offline: {e}")
            db.rollback()
        finally:
            db.close()

    async def sync_active_stations(self, active_ids: list[str]):
        db: Session = SessionLocal()
        try:
            # 1. Handle "Stuck Online" Stations
            # Find all stations that are is_online=True but NOT in active_ids
            query = db.query(ChargingStation.id).filter(ChargingStation.is_online == True)
            
            if active_ids:
                query = query.filter(ChargingStation.id.notin_(active_ids))
            
            station_ids_to_offline = [row[0] for row in query.all()]
            
            if station_ids_to_offline:
                # Update Connectors
                db.query(StationConnector).filter(
                    StationConnector.station_id.in_(station_ids_to_offline)
                ).update(
                    {StationConnector.status: ChargingStationStatus.Unknown},
                    synchronize_session=False
                )
                
                # Update Stations
                db.query(ChargingStation).filter(
                    ChargingStation.id.in_(station_ids_to_offline)
                ).update(
                    {ChargingStation.is_online: False},
                    synchronize_session=False
                )
                
                db.commit()
                logger.info(f"Watchdog: Forcefully set {len(station_ids_to_offline)} stuck stations to OFFLINE (Connectors: Unknown).")
            else:
                logger.debug("Watchdog: No stuck stations found.")

            # 2. Handle "Offline but Known Status" Connectors (Consistency Check)
            # Sometimes a station might be offline, but its connectors still show a status other than Unknown
            # (e.g. from manual DB edits or race conditions)
            
            # Subquery for offline station IDs
            offline_stations_subquery = db.query(ChargingStation.id).filter(ChargingStation.is_online == False).subquery()
            
            stuck_connectors_query = db.query(StationConnector).filter(
                StationConnector.station_id.in_(offline_stations_subquery),
                StationConnector.status != ChargingStationStatus.Unknown
            )
            
            updated_connectors_count = stuck_connectors_query.update(
                {StationConnector.status: ChargingStationStatus.Unknown},
                synchronize_session=False
            )
            
            if updated_connectors_count > 0:
                db.commit()
                logger.info(f"Watchdog: Fixed {updated_connectors_count} connectors with known status on OFFLINE stations.")
                
        except Exception as e:
            logger.error(f"Error syncing station states: {e}")
            db.rollback()
        finally:
            db.close()

station_service = StationService()
