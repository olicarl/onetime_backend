from pydantic import BaseModel
from typing import List, Optional, Any, Dict
from datetime import datetime
from app.models import ChargingStationStatus

# --- Auth Schemas ---

class LoginRequest(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: int
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
    parking_spot_id: int | None
    connectors: List[ConnectorStatus]
    active_session: Optional[ActiveSessionRef] = None

class ChargerUpdate(BaseModel):
    vendor: Optional[str] = None
    model: Optional[str] = None
    parking_spot_id: Optional[int] = None # To link/unlink

class ChargerDetail(BaseModel):
    id: str
    vendor: str | None
    model: str | None
    firmware_version: str | None
    is_online: bool
    last_heartbeat: datetime | None
    parking_spot_label: str | None
    parking_spot_id: int | None # Added for easier edit binding
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
    context: str | None


# --- User Management Schemas ---

class UserCreate(BaseModel):
    username: str
    password: str
    role: str = "admin"
    is_active: bool = True

class UserUpdate(BaseModel):
    password: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None

class UserOut(BaseModel):
    id: int
    username: str
    role: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# --- Renter Management Schemas ---

class RenterCreate(BaseModel):
    name: str
    contact_email: str
    phone_number: Optional[str] = None
    is_active: bool = True

class RenterUpdate(BaseModel):
    name: Optional[str] = None
    contact_email: Optional[str] = None
    phone_number: Optional[str] = None
    is_active: Optional[bool] = None

class RenterOut(BaseModel):
    id: int
    name: str
    contact_email: str
    phone_number: Optional[str] = None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# --- Parking Spot Management Schemas ---

class ParkingSpotCreate(BaseModel):
    label: str
    floor_level: Optional[str] = None
    renter_id: Optional[int] = None
    charging_station_id: Optional[str] = None

class ParkingSpotUpdate(BaseModel):
    label: Optional[str] = None
    floor_level: Optional[str] = None
    renter_id: Optional[int] = None
    charging_station_id: Optional[str] = None

class ParkingSpotOut(BaseModel):
    id: int
    label: str
    floor_level: Optional[str] = None
    renter_id: Optional[int] = None
    charging_station_id: Optional[str] = None
    
    # Optional nested details if needed
    renter: Optional[RenterOut] = None 
    # charging_station: ... avoid circular or too big

    class Config:
        from_attributes = True


# --- Authorization Token Management Schemas ---

from app.models import AuthorizationStatus

class AuthorizationTokenCreate(BaseModel):
    token: str
    renter_id: Optional[int] = None
    description: Optional[str] = None
    status: AuthorizationStatus = AuthorizationStatus.Accepted
    expiry_date: Optional[datetime] = None

class AuthorizationTokenUpdate(BaseModel):
    renter_id: Optional[int] = None
    description: Optional[str] = None
    status: Optional[AuthorizationStatus] = None
    expiry_date: Optional[datetime] = None

class AuthorizationTokenOut(BaseModel):
    token: str
    renter_id: Optional[int]
    description: Optional[str]
    status: AuthorizationStatus
    expiry_date: Optional[datetime]
    
    renter: Optional[RenterOut] = None

    class Config:
        from_attributes = True
