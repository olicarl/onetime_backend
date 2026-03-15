import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from app.main import app
from app.models import ChargingStation

def test_remote_stop_charger_not_found(client):
    response = client.post("/api/admin/chargers/INVALID_CS/remote-stop", json={"transaction_id": 123})
    assert response.status_code == 404

def test_remote_stop_offline(client, db_session):
    station = ChargingStation(id="CS-RS-001", is_online=False)
    db_session.add(station)
    db_session.commit()
    response = client.post("/api/admin/chargers/CS-RS-001/remote-stop", json={"transaction_id": 123})
    assert response.status_code == 400
    assert "offline" in response.json()["detail"]

