from app.database import SessionLocal
from app.models import OcppMessageLog
from app.config import logger
import json

class LoggingService:
    async def log_message(self, station_id: str, direction: str, message_type: str, action: str, payload: dict):
        db = SessionLocal()
        try:
            # Ensure payload is a dict or valid JSON structure
            if not isinstance(payload, (dict, list)):
                try:
                    payload = json.loads(payload)
                except:
                    pass
            
            log_entry = OcppMessageLog(
                station_id=station_id,
                direction=direction,
                message_type=message_type,
                action=action,
                payload=payload
            )
            db.add(log_entry)
            db.commit()
        except Exception as e:
            logger.error(f"Failed to log OCPP message: {e}")
        finally:
            db.close()

logging_service = LoggingService()
