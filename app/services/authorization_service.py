from datetime import datetime
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import AuthorizationToken, AuthorizationStatus
from app.config import logger

class AuthorizationService:
    
    async def authorize(self, id_tag: str, **kwargs):
        """
        Check if the token exists and is active.
        """
        db: Session = SessionLocal()
        try:
            token = db.query(AuthorizationToken).filter(AuthorizationToken.token == id_tag).first()
            
            if not token:
                logger.warning(f"Unknown token: {id_tag}")
                return {"id_tag_info": {"status": "Invalid"}}
            
            if token.status != AuthorizationStatus.Accepted:
                logger.warning(f"Token {id_tag} status: {token.status}")
                return {"id_tag_info": {"status": token.status}}
            
            if token.expiry_date and token.expiry_date < datetime.utcnow():
                 logger.warning(f"Token {id_tag} expired on {token.expiry_date}")
                 return {"id_tag_info": {"status": "Expired"}}

            return {
                "id_tag_info": {
                    "status": "Accepted",
                    "expiry_date": token.expiry_date.isoformat() if token.expiry_date else None,
                    "parent_id_tag": None
                }
            }
        except Exception as e:
            logger.error(f"Error authorizing {id_tag}: {e}")
            return {"id_tag_info": {"status": "Invalid"}}
        finally:
            db.close()

authorization_service = AuthorizationService()
