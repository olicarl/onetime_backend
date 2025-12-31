from pydantic import BaseModel
from typing import List, Optional, Any, Dict
from datetime import datetime
from app.models import ChargingStationStatus

# --- Auth Schemas ---

class LoginRequest(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    username: str
    role: str
    mode: str

# --- Admin / Charger Schemas ---

class ConnectorStatus(BaseModel):
    connector_id: int
    status: ChargingStationStatus
    current_transaction_id: Optional[int] = None

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

class ChargerDetail(BaseModel):
    id: str
    vendor: str | None
    model: str | None
    firmware_version: str | None
    is_online: bool
    last_heartbeat: datetime | None
    parking_spot_label: str | None
    connectors: List[ConnectorStatus]

class SessionLogItem(BaseModel):
    id: int
    transaction_id: int
    start_time: datetime
    end_time: datetime | None
    meter_start: int
    meter_stop: int | None
    total_energy: float | None
    stop_reason: str | None
    id_tag: str

class OcppLogItem(BaseModel):
    id: int
    timestamp: datetime
    direction: str
    message_type: str
    action: str
    payload: Dict | List | None

class MeterReadingItem(BaseModel):
    timestamp: datetime
    value: float
    unit: str | None
    measurand: str | None
    phase: str | None
    context: str | None
