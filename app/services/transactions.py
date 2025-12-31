from datetime import datetime
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import ChargingSession, MeterReading, AuthorizationToken, ChargingStation
from app.config import logger
from app.services.events import event_bus, Events

class TransactionService:
    
    def __init__(self):
        # Subscribe to events that might be relevant
        pass

    async def start_transaction(self, charger_id: str, connector_id: int, id_tag: str, meter_start: int, timestamp: str, **kwargs):
        """
        Handle StartTransaction:
        1. Validate token (again, usually).
        2. Create ChargingSession record.
        3. Return Accepted.
        """
        db: Session = SessionLocal()
        try:
            # Check Token
            token = db.query(AuthorizationToken).filter(AuthorizationToken.token == id_tag).first()
            status = "Accepted"
            if not token: # In strict mode this might fail, but for now we might allow unknown if configured?
                # For this assignment, assuming we rely on Authorize step or strict
                 status = "Invalid"
                 return {"transaction_id": 0, "id_tag_info": {"status": "Invalid"}}
            
            # Create Session
            # We assume unique transaction_id comes from station or we generate one?
            # OCPP 1.6: Central System generates TransactionId (integer).
            
            # Simple Auto-Increment via DB or explicit
            ts = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            
            # We need to construct the object first to flush and get ID? 
            # Or use a sequence. Let's rely on DB auto-increment for internal ID, but return that as transactionID.
            
            session = ChargingSession(
                station_id=charger_id,
                token_id=id_tag,
                # generate a random int for unique constraints if needed, or use DB ID after flush
                transaction_id=0, # Placeholder, will update after flush if possible or use sequence
                start_time=ts,
                meter_start=meter_start,
                total_energy_kwh=0.0
            )
            # Find a way to generate unique TransactionID safe for OCPP (integer)
            # Doing a quick search for max id
            
            # A cheat: Commit first empty to get ID? No, Constraints.
            # Use timestamp based integer?
            import time
            session.transaction_id = int(time.time() * 1000) % 2147483647 

            db.add(session)
            db.commit()
            db.refresh(session)
            
            logger.info(f"Started transaction {session.transaction_id} on {charger_id}/{connector_id}")
            
            return {
                "transaction_id": session.transaction_id,
                "id_tag_info": {"status": "Accepted", "expiry_date": None, "parent_id_tag": None}
            }

        except Exception as e:
            logger.error(f"Error starting transaction: {e}")
            return {"transaction_id": 0, "id_tag_info": {"status": "ConcurrentTx"}} # Or other error
        finally:
            db.close()

    async def stop_transaction(self, charger_id: str, meter_stop: int, timestamp: str, transaction_id: int, reason: str = None, **kwargs):
        """
        Handle StopTransaction:
        1. Find session.
        2. Update end time and meter stop.
        3. Calculate consumption.
        """
        db: Session = SessionLocal()
        try:
            session = db.query(ChargingSession).filter(ChargingSession.transaction_id == transaction_id).first()
            if not session:
                logger.warning(f"StopTransaction for unknown ID: {transaction_id}")
                return {"id_tag_info": {"status": "Expired"}} # Return generic info
            
            ts = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            session.end_time = ts
            session.meter_stop = meter_stop
            session.stop_reason = reason
            
            # Calculate Energy
            if meter_stop >= session.meter_start:
                consumed_wh = meter_stop - session.meter_start
                session.total_energy_kwh = consumed_wh / 1000.0
            
            db.commit()
            logger.info(f"Stopped transaction {transaction_id}, consumed {session.total_energy_kwh} kWh")
            
            return {"id_tag_info": {"status": "Accepted"}}
        except Exception as e:
            logger.error(f"Error stopping transaction {transaction_id}: {e}")
            return {"id_tag_info": {"status": "Invalid"}}
        finally:
            db.close()

    async def handle_meter_values(self, charger_id: str, payload: dict):
        """
        Process MeterValues payload (save to DB).
        """
        db: Session = SessionLocal()
        try:
             # ConnectorID is inside payload usually?
             # payload = { "connector_id": ..., "meter_value": [ ... ] }
             connector_id = payload.get("connector_id")
             transaction_id = payload.get("transaction_id")
             
             meter_values = payload.get("meter_value", [])
             
             for mv in meter_values:
                 timestamp_str = mv.get("timestamp")
                 ts = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
                 
                 sampled_values = mv.get("sampled_value", [])
                 for sv in sampled_values:
                     # Create Reading
                     reading = MeterReading(
                         transaction_id=transaction_id, # Can be None if not in transaction
                         timestamp=ts,
                         measurand=sv.get("measurand", "Energy.Active.Import.Register"),
                         value=sv.get("value"),
                         unit=sv.get("unit"),
                         phase=sv.get("phase"),
                         context=sv.get("context")
                     )
                     # If transaction_id is missing in payload, try to find active session for this connector?
                     # For now, if no transaction_id, we might skip or store with null if allowed.
                     # Our model enforces transaction_id NOT NULL for MeterReading? 
                     # Let's check model... -> yes nullable=False.
                     # So if no transaction_id, we can't save it easily without lookups.
                     # Simplification: Only save if transaction_id provided.
                     
                     if transaction_id:
                         db.add(reading)
            
             db.commit()
             logger.info(f"Saved {len(meter_values)} meter value records for {charger_id}")

        except Exception as e:
            logger.error(f"Error saving MeterValues: {e}")
        finally:
            db.close()

    async def data_transfer(self, vendor_id: str, message_id: str = None, data: str = None, **kwargs):
        """
        Handle DataTransfer.
        """
        logger.info(f"DataTransfer: vendor_id={vendor_id}, message_id={message_id}, data={data}")
        # Simplistic acceptance for EVerest specific polling
        if vendor_id == "org.openchargealliance.iso15118pnc":
             return {"status": "Accepted", "data": "{}"}
        
        return {"status": "Accepted", "data": None}

    async def security_event_notification(self, type: str, timestamp: str, tech_info: str = None, **kwargs):
        """
        Handle SecurityEventNotification.
        """
        logger.info(f"SecurityEvent: {type} at {timestamp}. Info: {tech_info}")
        # Just log for now
        pass

    async def log_status_notification(self, status: str, request_id: int, **kwargs):
         """
         Handle LogStatusNotification.
         """
         logger.info(f"LogStatus: {status} for Request {request_id}")
         pass

    async def sign_certificate(self, csr: str, **kwargs):
        """
        Handle SignCertificate.
        """
        logger.info(f"SignCertificate received for CSR length: {len(csr)}")
        # Mock response
        return {"status": "Accepted"}

    async def signed_firmware_status_notification(self, status: str, request_id: int, **kwargs):
        """
        Handle SignedFirmwareStatusNotification.
        """
        logger.info(f"SignedFirmwareStatus: {status} for Request {request_id}")
        pass

transaction_service = TransactionService()
