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
