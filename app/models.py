from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Float, Enum, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.database import Base

# Enums
class AuthorizationStatus(str, enum.Enum):
    Accepted = "Accepted"
    Blocked = "Blocked"
    Expired = "Expired"
    Invalid = "Invalid"
    ConcurrentTx = "ConcurrentTx"

class ChargingStationStatus(str, enum.Enum):
    Available = "Available"
    Preparing = "Preparing"
    Charging = "Charging"
    SuspendedEVSE = "SuspendedEVSE"
    SuspendedEV = "SuspendedEV"
    Finishing = "Finishing"
    Reserved = "Reserved"
    Unavailable = "Unavailable"
    Faulted = "Faulted"
    Unknown = "Unknown"

# Models

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, default="admin", nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Renter(Base):
    __tablename__ = "renters"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    contact_email = Column(String, nullable=False)
    phone_number = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    parking_spots = relationship("ParkingSpot", back_populates="renter")
    authorization_tokens = relationship("AuthorizationToken", back_populates="renter")


class ParkingSpot(Base):
    __tablename__ = "parking_spots"

    id = Column(Integer, primary_key=True, index=True)
    label = Column(String, unique=True, nullable=False)
    floor_level = Column(String, nullable=True)
    renter_id = Column(Integer, ForeignKey("renters.id"), nullable=True)
    charging_station_id = Column(String, ForeignKey("charging_stations.id"), unique=True, nullable=True)

    renter = relationship("Renter", back_populates="parking_spots")
    charging_station = relationship("ChargingStation", back_populates="parking_spot")


class ChargingStation(Base):
    __tablename__ = "charging_stations"

    id = Column(String, primary_key=True, index=True) # chargePointId
    is_online = Column(Boolean, default=False)
    last_heartbeat = Column(DateTime, nullable=True)
    model = Column(String, nullable=True)
    vendor = Column(String, nullable=True)
    firmware_version = Column(String, nullable=True)

    parking_spot = relationship("ParkingSpot", back_populates="charging_station", uselist=False)
    sessions = relationship("ChargingSession", back_populates="station")
    connectors = relationship("StationConnector", back_populates="station")
    configurations = relationship("StationConfiguration", back_populates="station")
    boot_logs = relationship("BootLog", back_populates="station")
    ocpp_logs = relationship("OcppMessageLog", back_populates="station")


class AuthorizationToken(Base):
    __tablename__ = "authorization_tokens"

    token = Column(String, primary_key=True, index=True) # idTag
    renter_id = Column(Integer, ForeignKey("renters.id"), nullable=False)
    status = Column(Enum(AuthorizationStatus), default=AuthorizationStatus.Accepted)
    expiry_date = Column(DateTime, nullable=True)
    description = Column(String, nullable=True)

    renter = relationship("Renter", back_populates="authorization_tokens")
    sessions = relationship("ChargingSession", back_populates="token_rel")


class ChargingSession(Base):
    __tablename__ = "charging_sessions"

    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(Integer, unique=True, nullable=False, index=True)
    station_id = Column(String, ForeignKey("charging_stations.id"), nullable=False)
    connector_id = Column(Integer, nullable=True) # Added for tracking which connector
    token_id = Column(String, ForeignKey("authorization_tokens.token"), nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=True)
    meter_start = Column(Integer, nullable=False) # Wh
    meter_stop = Column(Integer, nullable=True) # Wh
    total_energy_kwh = Column(Float, nullable=True)
    stop_reason = Column(String, nullable=True)

    station = relationship("ChargingStation", back_populates="sessions")
    token_rel = relationship("AuthorizationToken", back_populates="sessions")
    meter_readings = relationship("MeterReading", back_populates="session")


class StationConnector(Base):
    __tablename__ = "station_connectors"

    station_id = Column(String, ForeignKey("charging_stations.id"), primary_key=True)
    connector_id = Column(Integer, primary_key=True)
    status = Column(Enum(ChargingStationStatus), default=ChargingStationStatus.Unavailable)
    error_code = Column(String, default="NoError")
    last_updated = Column(DateTime, default=datetime.utcnow)

    station = relationship("ChargingStation", back_populates="connectors")


class MeterReading(Base):
    __tablename__ = "meter_readings"

    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(Integer, ForeignKey("charging_sessions.transaction_id"), nullable=False)
    timestamp = Column(DateTime, nullable=False)
    measurand = Column(String, nullable=False)
    value = Column(String, nullable=False)
    unit = Column(String, nullable=True)
    phase = Column(String, nullable=True)
    context = Column(String, nullable=True)

    session = relationship("ChargingSession", back_populates="meter_readings")


class StationConfiguration(Base):
    __tablename__ = "station_configurations"

    station_id = Column(String, ForeignKey("charging_stations.id"), primary_key=True)
    key = Column(String, primary_key=True)
    value = Column(String, nullable=True)
    readonly = Column(Boolean, default=False)

    station = relationship("ChargingStation", back_populates="configurations")


class BootLog(Base):
    __tablename__ = "boot_logs"

    id = Column(Integer, primary_key=True, index=True)
    station_id = Column(String, ForeignKey("charging_stations.id"), nullable=False)
    boot_time = Column(DateTime, default=datetime.utcnow)
    model = Column(String, nullable=True)
    vendor = Column(String, nullable=True)
    firmware_version = Column(String, nullable=True)
    ip_address = Column(String, nullable=True)

    station = relationship("ChargingStation", back_populates="boot_logs")


class OcppMessageLog(Base):
    __tablename__ = "ocpp_message_logs"

    id = Column(Integer, primary_key=True, index=True)
    station_id = Column(String, ForeignKey("charging_stations.id"), nullable=False)
    message_type = Column(String, nullable=False) # e.g. CALL, CALLRESULT, CALLERROR
    action = Column(String, nullable=False) # e.g. BootNotification
    direction = Column(String, nullable=False) # Incoming, Outgoing
    payload = Column(JSON, nullable=True) # The JSON payload
    timestamp = Column(DateTime, default=datetime.utcnow)

    station = relationship("ChargingStation", back_populates="ocpp_logs")

