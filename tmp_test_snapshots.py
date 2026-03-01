from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import AuthorizationToken, ChargingSession, Renter, ChargingStation
from app.services.transactions import transaction_service
from datetime import datetime
import asyncio

async def test_snapshot_logic():
    db = SessionLocal()
    try:
        # Create test data
        renter = Renter(name="Snapshot Renter", contact_email="snap@test.com")
        db.add(renter)
        db.commit()

        token = AuthorizationToken(token="TAG_SNAP_TEST", renter_id=renter.id)
        db.add(token)

        station = ChargingStation(id="CP_SNAP", is_online=True)
        db.add(station)
        db.commit()
        
        # Call start_transaction 
        res = await transaction_service.start_transaction(
            charger_id="CP_SNAP", 
            connector_id=1, 
            id_tag="TAG_SNAP_TEST", 
            meter_start=100, 
            timestamp=datetime.utcnow().isoformat() + "Z"
        )
        
        tx_id = res["transaction_id"]
        
        # Verify Session has snapshots
        session = db.query(ChargingSession).filter(ChargingSession.transaction_id == tx_id).first()
        
        assert session.token_snapshot == "TAG_SNAP_TEST"
        assert session.renter_name_snapshot == "Snapshot Renter"
        assert session.renter_email_snapshot == "snap@test.com"
        print("Success! Snapshot fields exist on new session.")
        
        # Test frontend endpoints using these fields (via our deletion logic)
        # Delete the token
        db_token = db.query(AuthorizationToken).filter(AuthorizationToken.token == "TAG_SNAP_TEST").first()
        for s in db_token.sessions:
            s.token_id = None
        db.delete(db_token)
        db.commit()
        
        # Verify Session still has snapshots
        db.refresh(session)
        assert session.token_id is None
        assert session.token_snapshot == "TAG_SNAP_TEST"
        assert session.renter_name_snapshot == "Snapshot Renter"
        print("Success! After token deletion, session keeps snapshot data.")

        # Cleanup
        db.delete(session)
        db.delete(station)
        db.delete(renter)
        db.commit()

    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(test_snapshot_logic())
