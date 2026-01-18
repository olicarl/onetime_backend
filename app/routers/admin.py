from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import ChargingStation, ChargingStationStatus, ChargingSession
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

router = APIRouter(prefix="/api/admin", tags=["Admin"])

from app.schemas import (
    ConnectorStatus, 
    ChargerDashboardItem, 
    ChargerDetail, 
    ChargerUpdate, # Added
    SessionLogItem, 
    OcppLogItem, 
    MeterReadingItem,
    ActiveSessionRef
)

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
            parking_spot_id=c.parking_spot.id if c.parking_spot else None,
            connectors=connectors_data,
            active_session=active_sess_data
        ))
        
    return result

@router.get("/system-info")
def get_system_info():
    import socket
    try:
        # Connect to a public DNS server to find the local IP used for routing
        # This doesn't actually send data
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0.1)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
    except Exception:
        local_ip = "127.0.0.1"
    
    return {"ip_address": local_ip}

# --- Charger Details ---



@router.get("/chargers/{charger_id}", response_model=ChargerDetail)
def get_charger_detail(charger_id: str, db: Session = Depends(get_db)):
    c = db.query(ChargingStation).filter(ChargingStation.id == charger_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Charger not found")
        
    # Find active sessions for this station
    active_sessions = (
        db.query(ChargingSession)
        .filter(
            ChargingSession.station_id == charger_id, 
            ChargingSession.end_time.is_(None)
        )
        .all()
    )
    # Map connector_id -> transaction_id
    active_map = {}
    for s in active_sessions:
        if s.connector_id is not None:
             active_map[s.connector_id] = s.transaction_id
        
    connectors_data = []
    for conn in c.connectors:
        tx_id = active_map.get(conn.connector_id)
        connectors_data.append(ConnectorStatus(
            connector_id=conn.connector_id, 
            status=conn.status,
            current_transaction_id=tx_id
        ))
    
    spot_label = c.parking_spot.label if c.parking_spot else None
    
    return ChargerDetail(
        id=c.id,
        vendor=c.vendor,
        model=c.model,
        firmware_version=c.firmware_version,
        is_online=c.is_online,
        last_heartbeat=c.last_heartbeat,
        parking_spot_label=spot_label,
        connectors=connectors_data
    )



@router.get("/chargers/{charger_id}/sessions", response_model=List[SessionLogItem])
def get_charger_sessions(charger_id: str, db: Session = Depends(get_db)):
    sessions = (
        db.query(ChargingSession)
        .filter(ChargingSession.station_id == charger_id)
        .order_by(ChargingSession.start_time.desc())
        .limit(50)
        .all()
    )
    
    result = []
    for s in sessions:
        # Calculate total energy if not stored (optional fallback)
        total = s.total_energy_kwh
        if total is None and s.meter_stop and s.meter_start:
             total = (s.meter_stop - s.meter_start) / 1000.0
             
        result.append(SessionLogItem(
            id=s.id,
            transaction_id=s.transaction_id,
            start_time=s.start_time,
            end_time=s.end_time,
            meter_start=s.meter_start,
            meter_stop=s.meter_stop,
            total_energy=total,
            stop_reason=s.stop_reason,
            id_tag=s.token_id
        ))
    return result



@router.get("/chargers/{charger_id}/logs", response_model=List[OcppLogItem])
def get_charger_logs(charger_id: str, db: Session = Depends(get_db)):
    # Import here to avoid circular dependencies if any, 
    # though models are in same file usually.
    from app.models import OcppMessageLog
    
    logs = (
        db.query(OcppMessageLog)
        .filter(OcppMessageLog.station_id == charger_id)
        .order_by(OcppMessageLog.timestamp.desc())
        .limit(100)
        .all()
    )
    
    return [
        OcppLogItem(
            id=l.id,
            timestamp=l.timestamp,
            direction=l.direction,
            message_type=l.message_type,
            action=l.action,
            payload=l.payload
        )
        for l in logs
    ]

@router.put("/chargers/{charger_id}", response_model=ChargerDetail)
def update_charger(charger_id: str, charger: ChargerUpdate, db: Session = Depends(get_db)):
    db_charger = db.query(ChargingStation).filter(ChargingStation.id == charger_id).first()
    if not db_charger:
        raise HTTPException(status_code=404, detail="Charger not found")

    if charger.vendor is not None:
        db_charger.vendor = charger.vendor
    if charger.model is not None:
        db_charger.model = charger.model
        
    # Handle Parking Spot Linking
    # Note: ParkingSpot holds the FK charging_station_id
    if charger.parking_spot_id is not None:
        from app.models import ParkingSpot
        # 1. Clear any existing link for this charger on OTHER spots (since 1:1)
        # We need to find if this charger is already linked to a spot
        existing_spot = db.query(ParkingSpot).filter(ParkingSpot.charging_station_id == charger_id).first()
        if existing_spot and existing_spot.id != charger.parking_spot_id:
            existing_spot.charging_station_id = None
        
        # 2. Link the new spot
        # If charger.parking_spot_id is 0 or -1 (unlinking convention?), or we can just assume if passed we link.
        # If we interpret None as "no change", then unlinking must be done explicitly?
        # But for now, let's strictly link if ID is valid.
        # If user wants to unlink, they would update the parking spot directly to set charger=None.
        # But let's check if we can handle unlinking here. 
        # For now, simplistic: if valid ID, link it.
        
        target_spot = db.query(ParkingSpot).filter(ParkingSpot.id == charger.parking_spot_id).first()
        if target_spot:
             # Ensure this spot doesn't already have another charger?
             # Or just overwrite. Overwriting is usually preferred in admin UI.
             target_spot.charging_station_id = charger_id
    
    # If we wanted to allow unlinking via this endpoint, we'd need a specific value logic since this is a PATCH-like update where None means missing.
    
    db.commit()
    db.refresh(db_charger)
    
    # Construct response manually or re-query to get relationships populated
    # OR rely on ORM
    
    connectors_data = [
        ConnectorStatus(connector_id=conn.connector_id, status=conn.status)
        for conn in db_charger.connectors
    ]
    
    return ChargerDetail(
        id=db_charger.id,
        vendor=db_charger.vendor,
        model=db_charger.model,
        firmware_version=db_charger.firmware_version,
        is_online=db_charger.is_online,
        last_heartbeat=db_charger.last_heartbeat,
        parking_spot_label=db_charger.parking_spot.label if db_charger.parking_spot else None,
        parking_spot_id=db_charger.parking_spot.id if db_charger.parking_spot else None,
        connectors=connectors_data
    )

@router.delete("/chargers/{charger_id}")
def delete_charger(charger_id: str, db: Session = Depends(get_db)):
    db_charger = db.query(ChargingStation).filter(ChargingStation.id == charger_id).first()
    if not db_charger:
        raise HTTPException(status_code=404, detail="Charger not found")

    if db_charger.is_online:
        raise HTTPException(status_code=400, detail="Cannot delete an online charger. Please disconnect it first.")

    # Unlink from parking spot if any (Constraint management)
    # Although ON DELETE SET NULL might be configured, let's be explicit
    if db_charger.parking_spot:
        db_charger.parking_spot.charging_station_id = None
        
    db.delete(db_charger)
    db.commit()
    return {"message": "Charger deleted"}

# Session details (Graph data)


@router.get("/sessions/{transaction_id}/readings", response_model=List[MeterReadingItem])
def get_session_readings(transaction_id: int, db: Session = Depends(get_db)):
    from app.models import MeterReading
    
    readings = (
        db.query(MeterReading)
        .filter(MeterReading.transaction_id == transaction_id)
        .order_by(MeterReading.timestamp.asc())
        .all()
    )
    
    clean_readings = []
    for r in readings:
        try:
            val = float(r.value)
            clean_readings.append(MeterReadingItem(
                timestamp=r.timestamp,
                value=val,
                unit=r.unit,
                measurand=r.measurand,
                phase=r.phase,
                context=r.context
            ))
        except:
            pass
            
    return clean_readings


# --- User Management Endpoints ---

from app.schemas import UserCreate, UserUpdate, UserOut
from app.models import User
from app.security import get_password_hash

@router.get("/users", response_model=List[UserOut])
def get_users(db: Session = Depends(get_db)):
    return db.query(User).all()

@router.post("/users", response_model=UserOut)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    hashed_password = get_password_hash(user.password)
    new_user = User(
        username=user.username,
        password_hash=hashed_password,
        role=user.role,
        is_active=user.is_active
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.put("/users/{user_id}", response_model=UserOut)
def update_user(user_id: int, user: UserUpdate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.password:
        db_user.password_hash = get_password_hash(user.password)
    if user.role is not None:
        db_user.role = user.role
    if user.is_active is not None:
        db_user.is_active = user.is_active
        
    db.commit()
    db.refresh(db_user)
    return db_user

@router.delete("/users/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    db.delete(db_user)
    db.commit()
    return {"message": "User deleted"}


# --- Renter Management Endpoints ---

from app.schemas import RenterCreate, RenterUpdate, RenterOut
from app.models import Renter

@router.get("/renters", response_model=List[RenterOut])
def get_renters(db: Session = Depends(get_db)):
    return db.query(Renter).all()

@router.post("/renters", response_model=RenterOut)
def create_renter(renter: RenterCreate, db: Session = Depends(get_db)):
    # Basic check if email exists?
    # Basic check if email exists?
    # db_renter = db.query(Renter).filter(Renter.contact_email == renter.contact_email).first()
    # if db_renter:
    #     raise HTTPException(status_code=400, detail="Email already registered")

    new_renter = Renter(
        name=renter.name,
        contact_email=renter.contact_email,
        phone_number=renter.phone_number,
        is_active=renter.is_active
    )
    db.add(new_renter)
    db.commit()
    db.refresh(new_renter)
    return new_renter

@router.put("/renters/{renter_id}", response_model=RenterOut)
def update_renter(renter_id: int, renter: RenterUpdate, db: Session = Depends(get_db)):
    db_renter = db.query(Renter).filter(Renter.id == renter_id).first()
    if not db_renter:
        raise HTTPException(status_code=404, detail="Renter not found")

    if renter.name is not None:
        db_renter.name = renter.name
    if renter.contact_email is not None:
        db_renter.contact_email = renter.contact_email
    if renter.phone_number is not None:
        db_renter.phone_number = renter.phone_number
    if renter.is_active is not None:
        db_renter.is_active = renter.is_active

    db.commit()
    db.refresh(db_renter)
    return db_renter

@router.delete("/renters/{renter_id}")
def delete_renter(renter_id: int, db: Session = Depends(get_db)):
    db_renter = db.query(Renter).filter(Renter.id == renter_id).first()
    if not db_renter:
        raise HTTPException(status_code=404, detail="Renter not found")

    # Unlink dependencies manually to avoid FK constraint errors
    # 1. Unlink Parking Spots
    for spot in db_renter.parking_spots:
        spot.renter_id = None
        
    # 2. Unlink Auth Tokens
    for token in db_renter.authorization_tokens:
        token.renter_id = None

    try:
        db.delete(db_renter)
        db.commit()
    except Exception as e:
        db.rollback()
        # Log error in real app
        raise HTTPException(status_code=400, detail="Cannot delete renter due to dependencies or DB error")
        
    return {"message": "Renter deleted"}


# --- Parking Spot Management Endpoints ---

from app.schemas import ParkingSpotCreate, ParkingSpotUpdate, ParkingSpotOut
from app.models import ParkingSpot

@router.get("/parking-spots", response_model=List[ParkingSpotOut])
def get_parking_spots(db: Session = Depends(get_db)):
    return db.query(ParkingSpot).all()

@router.post("/parking-spots", response_model=ParkingSpotOut)
def create_parking_spot(spot: ParkingSpotCreate, db: Session = Depends(get_db)):
    db_spot = db.query(ParkingSpot).filter(ParkingSpot.label == spot.label).first()
    if db_spot:
        raise HTTPException(status_code=400, detail="Parking Spot label already exists")

    new_spot = ParkingSpot(
        label=spot.label,
        floor_level=spot.floor_level,
        renter_id=spot.renter_id,
        charging_station_id=spot.charging_station_id
    )
    db.add(new_spot)
    db.commit()
    db.refresh(new_spot)
    return new_spot

@router.put("/parking-spots/{spot_id}", response_model=ParkingSpotOut)
def update_parking_spot(spot_id: int, spot: ParkingSpotUpdate, db: Session = Depends(get_db)):
    db_spot = db.query(ParkingSpot).filter(ParkingSpot.id == spot_id).first()
    if not db_spot:
        raise HTTPException(status_code=404, detail="Parking spot not found")

    if spot.label is not None:
        db_spot.label = spot.label
    if spot.floor_level is not None:
        db_spot.floor_level = spot.floor_level
    
    # Allow setting to None/null if explicitly sent, or changing value
    # We need to handle optional fields correctly. 
    # This naive update assumes if it's sent, update it.
    if spot.renter_id is not None:
        # 0 or -1 could mean 'unlink', but pydantic sends None if missing. 
        # If we want to unlink, we might need explicit field logic.
        # For now let's assume valid ID or existing. 
        # If user wants to unlink, we might need a specific action or handle nullable
        db_spot.renter_id = spot.renter_id
        
    if spot.charging_station_id is not None:
        db_spot.charging_station_id = spot.charging_station_id

    # Handle unlinking logic if needed (e.g. passing explicit nulls in update? Pydantic strips None usually)
    # A robust implementation would differentiate "unset" vs "set to null".
    # For a simple start:
    # If the user sends a specific value in a "unlink_renter" flag or similar, logic can handle it.
    # Alternatively, use a separate UNSET object.
    # We will stick to simple updates for now.

    db.commit()
    db.refresh(db_spot)
    return db_spot

@router.delete("/parking-spots/{spot_id}")
def delete_parking_spot(spot_id: int, db: Session = Depends(get_db)):
    db_spot = db.query(ParkingSpot).filter(ParkingSpot.id == spot_id).first()
    if not db_spot:
        raise HTTPException(status_code=404, detail="Parking spot not found")

    try:
        db.delete(db_spot)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail="Cannot delete parking spot due to DB reference or constraint.")

    return {"message": "Parking spot deleted"}


# --- Authorization Token Management Endpoints ---

from app.schemas import AuthorizationTokenCreate, AuthorizationTokenUpdate, AuthorizationTokenOut
from app.models import AuthorizationToken

@router.get("/auth-tokens", response_model=List[AuthorizationTokenOut])
def get_auth_tokens(db: Session = Depends(get_db)):
    return db.query(AuthorizationToken).all()

@router.post("/auth-tokens", response_model=AuthorizationTokenOut)
def create_auth_token(token_data: AuthorizationTokenCreate, db: Session = Depends(get_db)):
    db_token = db.query(AuthorizationToken).filter(AuthorizationToken.token == token_data.token).first()
    if db_token:
        # If it exists (maybe unknown), update it? Or error?
        # User might want to 'claim' an unknown token.
        # If status is Unknown, we can update it.
        # But simple CRUD usually errors on duplicate ID.
        # Let's check status just in case, but standard is 400.
        raise HTTPException(status_code=400, detail="Token already exists")

    new_token = AuthorizationToken(
        token=token_data.token,
        renter_id=token_data.renter_id,
        description=token_data.description,
        status=token_data.status,
        expiry_date=token_data.expiry_date
    )
    db.add(new_token)
    db.commit()
    db.refresh(new_token)
    return new_token

@router.put("/auth-tokens/{token}", response_model=AuthorizationTokenOut)
def update_auth_token(token: str, token_data: AuthorizationTokenUpdate, db: Session = Depends(get_db)):
    db_token = db.query(AuthorizationToken).filter(AuthorizationToken.token == token).first()
    if not db_token:
        raise HTTPException(status_code=404, detail="Token not found")
        
    if token_data.renter_id is not None:
        # If 0 or -1 is sent to unlink?
        # Assuming frontend sends null or omits if no change. 
        # If explicit null is desired, we need unset logic.
        # As per schema, it's Optional[int]. 
        # If user wants to unlink, we assume they might send a special value or we can't easily detect 'set to null' with just Optional in Pydantic v1/defaults.
        # But we made sure renter_id is nullable in DB.
        # Let's assume if it's passed it's a value. If they want to unlink, maybe handle 0?
        # For now, let's just update if value is present.
        # NOTE: standard pydantic .dict(exclude_unset=True) approach in service layer is better.
        # Here we do manual checks.
        db_token.renter_id = token_data.renter_id
        
    if token_data.description is not None:
        db_token.description = token_data.description
    
    if token_data.status is not None:
        db_token.status = token_data.status
        
    if token_data.expiry_date is not None:
        db_token.expiry_date = token_data.expiry_date

    db.commit()
    db.refresh(db_token)
    return db_token

@router.delete("/auth-tokens/{token}")
def delete_auth_token(token: str, db: Session = Depends(get_db)):
    db_token = db.query(AuthorizationToken).filter(AuthorizationToken.token == token).first()
    if not db_token:
        raise HTTPException(status_code=404, detail="Token not found")
        
    # Check for sessions?
    if db_token.sessions:
        raise HTTPException(status_code=400, detail="Cannot delete token with associated charging sessions")

    try:
        db.delete(db_token)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail="Cannot delete token")
        
    return {"message": "Token deleted"}
