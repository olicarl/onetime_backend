from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import AuthorizationToken, ChargingSession, Renter, ChargingStation
from datetime import datetime

def test_deletion_logic():
    db = SessionLocal()
    try:
        # Check if there is a session, token, renter we can use, or create one
        renter = Renter(name="Script Renter", contact_email="test1@test.com")
        db.add(renter)
        db.commit()

        token = AuthorizationToken(token="TEST_TAG_SCRIPT", renter_id=renter.id)
        db.add(token)

        station = ChargingStation(id="CP_SCRIPT_TEST", is_online=True)
        db.add(station)
        
        session = ChargingSession(
            transaction_id=999999,
            station_id="CP_SCRIPT_TEST",
            token_id="TEST_TAG_SCRIPT",
            start_time=datetime.utcnow(),
            meter_start=0
        )
        db.add(session)
        db.commit()
        
        # Now try the deletion logic exactly as it is in admin.py
        db_token = db.query(AuthorizationToken).filter(AuthorizationToken.token == "TEST_TAG_SCRIPT").first()
        
        # Nullify token_id for associated sessions to maintain history
        for s in db_token.sessions:
            s.token_id = None
    
        db.delete(db_token)
        db.commit()

        # Check if session is kept and token_id is None
        kept_session = db.query(ChargingSession).filter(ChargingSession.transaction_id == 999999).first()
        assert kept_session.token_id is None
        print("Success! Token was deleted and session was kept with token_id=None.")

        # Cleanup
        db.delete(kept_session)
        db.delete(station)
        db.delete(renter)
        db.commit()

    finally:
        db.close()

if __name__ == "__main__":
    test_deletion_logic()
