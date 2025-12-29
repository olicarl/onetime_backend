from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import ChargingStation, ChargingStationStatus, ChargingSession
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter(prefix="/api/admin", tags=["Admin"])

class ConnectorStatus(BaseModel):
    connector_id: int
    status: ChargingStationStatus

class ActiveSessionRef(BaseModel):
    transaction_id: int
    renter_name: str
    energy_consumed: int # Wh

class ChargerDashboardItem(BaseModel):
    id: str
    vendor: str | None
    model: str | None
    is_online: bool
    parking_spot_label: str | None
    connectors: List[ConnectorStatus]
    active_session: Optional[ActiveSessionRef] = None

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/chargers", response_model=List[ChargerDashboardItem])
def get_chargers(db: Session = Depends(get_db)):
    chargers = db.query(ChargingStation).all()
    result = []
    
    for c in chargers:
        # Get Connectors
        connectors_data = [
            ConnectorStatus(connector_id=conn.connector_id, status=conn.status)
            for conn in c.connectors
        ]
        
        # Get Active Session (if any)
        active_sess_model = (
            db.query(ChargingSession)
            .filter(ChargingSession.station_id == c.id, ChargingSession.end_time.is_(None))
            .first()
        )
        
        active_sess_data = None
        if active_sess_model:
            # Join with Token -> Renter to get name? 
            # For simplicity, accessing relations:
            renter_name = "Unknown"
            if active_sess_model.token_rel and active_sess_model.token_rel.renter:
                renter_name = active_sess_model.token_rel.renter.name
            
            # Calculate energy consumed so far
            current_energy = 0
            if active_sess_model.meter_readings:
                # Naive: last reading - start. Real world is more complex.
                last_reading = active_sess_model.meter_readings[-1]
                try:
                    current_energy = int(float(last_reading.value)) - active_sess_model.meter_start
                except:
                    pass

            active_sess_data = ActiveSessionRef(
                transaction_id=active_sess_model.transaction_id,
                renter_name=renter_name,
                energy_consumed=current_energy
            )
            
        # Get Parking Spot Label
        spot_label = c.parking_spot.label if c.parking_spot else None

        result.append(ChargerDashboardItem(
            id=c.id,
            vendor=c.vendor,
            model=c.model,
            is_online=c.is_online,
            parking_spot_label=spot_label,
            connectors=connectors_data,
            active_session=active_sess_data
        ))
        
    return result
