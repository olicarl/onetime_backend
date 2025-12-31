from fastapi import status
from unittest.mock import MagicMock
from app.models import ChargingStation, ChargingStationStatus, StationConnector, ParkingSpot

def test_get_chargers(client, db_session, auth_headers):
    # Seed DB
    station = ChargingStation(id="CP1", is_online=True, model="TestModel", vendor="TestVendor")
    db_session.add(station)
    connector = StationConnector(station_id="CP1", connector_id=1, status=ChargingStationStatus.Available)
    db_session.add(connector)
    spot = ParkingSpot(label="A1", charging_station_id="CP1")
    db_session.add(spot)
    db_session.commit()
    
    response = client.get("/api/admin/chargers", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    # Check if our seeded station is in the list
    found = next((item for item in data if item["id"] == "CP1"), None)
    assert found is not None
    assert found["parking_spot_label"] == "A1"
    assert len(found["connectors"]) == 1

def test_get_charger_sessions(client, db_session, auth_headers):
    # Setup
    from app.models import ChargingSession, AuthorizationToken, Renter
    from datetime import datetime
    
    # Needs dependencies: Token -> Renter
    renter = Renter(name="Test Renter", contact_email="test@example.com")
    db_session.add(renter)
    db_session.commit()
    
    token = AuthorizationToken(token="TEST_TAG", renter_id=renter.id)
    db_session.add(token)
    
    station = ChargingStation(id="CP_SESS", is_online=True)
    db_session.add(station)
    
    session = ChargingSession(
        transaction_id=12345,
        station_id="CP_SESS",
        token_id="TEST_TAG",
        start_time=datetime.utcnow(),
        meter_start=0
    )
    db_session.add(session)
    db_session.commit()
    
    response = client.get("/api/admin/chargers/CP_SESS/sessions", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) >= 1
    assert data[0]["transaction_id"] == 12345

def test_get_charger_logs(client, db_session, auth_headers):
    from app.models import OcppMessageLog
    
    station = ChargingStation(id="CP_LOGS", is_online=True)
    db_session.add(station)
    
    log = OcppMessageLog(
        station_id="CP_LOGS",
        message_type="CALL",
        action="BootNotification",
        direction="Incoming",
        payload={}
    )
    db_session.add(log)
    db_session.commit()
    
    response = client.get("/api/admin/chargers/CP_LOGS/logs", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 1
    assert data[0]["action"] == "BootNotification"

def test_get_session_readings(client, db_session, auth_headers):
    from app.models import MeterReading, ChargingSession, AuthorizationToken, Renter, ChargingStation
    from datetime import datetime

    # Need to create session hierarchy to satisfy constraints if any (Foreign Keys)
    # The models show MeterReading.transaction_id FK to sessions.
    # We can reuse the session setup logic if we want, or just be minimal if constraints assume existing objects.
    
    # Re-using previous approach (distinct objects for isolation)
    renter = Renter(name="Test Renter 2", contact_email="t2@example.com")
    db_session.add(renter)
    db_session.commit()
    token = AuthorizationToken(token="TAG2", renter_id=renter.id)
    db_session.add(token)
    station = ChargingStation(id="CP_READ", is_online=True)
    db_session.add(station)
    session = ChargingSession(
        transaction_id=999, 
        station_id="CP_READ", 
        token_id="TAG2", 
        start_time=datetime.utcnow(), 
        meter_start=0
    )
    db_session.add(session)
    
    reading = MeterReading(
        transaction_id=999,
        timestamp=datetime.utcnow(),
        measurand="Energy.Active.Import.Register",
        value="1000"
    )
    db_session.add(reading)
    db_session.commit()
    
    response = client.get("/api/admin/sessions/999/readings", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 1
    assert data[0]["value"] == 1000.0

def test_get_charger_detail(client, db_session, auth_headers):
    station = ChargingStation(id="CP2", is_online=False, model="TestModel2")
    db_session.add(station)
    db_session.commit()
    
    response = client.get("/api/admin/chargers/CP2", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == "CP2"
    assert data["model"] == "TestModel2"

def test_get_charger_detail_not_found(client, auth_headers):
    response = client.get("/api/admin/chargers/NONEXISTENT", headers=auth_headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND

def test_get_system_info(client, auth_headers):
    response = client.get("/api/admin/system-info", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    assert "ip_address" in response.json()
