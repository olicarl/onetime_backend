import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
from app.main import app
from app.models import BillingSettings, Renter, AuthorizationToken, ChargingSession, Invoice, BillingPeriodicity
from app.database import get_db, Base

def override_get_db():
    # In a real pytest environment, this would yield a test database session
    # For now, we mock the dependency if needed in the test setup
    pass

client = TestClient(app)

def test_get_billing_settings(db_session):
    # This assumes db_session is a fixture providing a fresh DB
    response = client.get("/api/billing/settings")
    assert response.status_code == 200
    data = response.json()
    assert "company_name" in data
    assert "iban" in data
    assert "price_per_kwh" in data

def test_update_billing_settings(db_session):
    payload = {
        "company_name": "Test Company",
        "iban": "CH123456789",
        "address": "Test Street 1, 1000 City",
        "periodicity": "Monthly",
        "price_per_kwh": 0.45
    }
    response = client.put("/api/billing/settings", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["company_name"] == "Test Company"
    assert data["price_per_kwh"] == 0.45

def test_generate_manual_invoice(db_session):
    # 1. Setup Data
    settings = BillingSettings(company_name="A", iban="B", address="C", periodicity=BillingPeriodicity.Monthly, price_per_kwh=0.50)
    db_session.add(settings)
    
    renter = Renter(name="John Doe", contact_email="john@example.com")
    db_session.add(renter)
    db_session.commit()
    
    token = AuthorizationToken(token="DEADBEEF", renter_id=renter.id)
    db_session.add(token)
    db_session.commit()
    
    # Create an unbilled session
    session = ChargingSession(
        transaction_id=1001,
        station_id="CS-001",
        token_id="DEADBEEF",
        start_time=datetime.now() - timedelta(days=2),
        end_time=datetime.now() - timedelta(days=2, hours=-1),
        meter_start=0,
        meter_stop=10000, # 10 kWh
        total_energy_kwh=10.0
    )
    db_session.add(session)
    db_session.commit()
    
    # 2. Add some headers to bypass auth if needed for tests, or use TestClient
    payload = {
        "renter_id": renter.id,
        "end_date": datetime.now().isoformat()
    }
    response = client.post("/api/billing/invoices/generate", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    assert "invoice_id" in data
    assert data["invoice_id"] is not None
    
    # Verify invoice was created correctly
    invoice = db_session.query(Invoice).filter_by(id=data["invoice_id"]).first()
    assert invoice is not None
    assert invoice.amount_due == 5.0 # 10 kWh * 0.50 CHF

def test_mark_invoice_paid(db_session):
    # Setup Invoice
    renter = Renter(name="Jane", contact_email="jane@example.com")
    db_session.add(renter)
    db_session.commit()
    
    invoice = Invoice(
        renter_id=renter.id,
        period_start=datetime.now(),
        period_end=datetime.now(),
        amount_due=10.0,
        is_paid=False
    )
    db_session.add(invoice)
    db_session.commit()
    
    response = client.post(f"/api/billing/invoices/{invoice.id}/mark-paid")
    assert response.status_code == 200
    assert response.json()["is_paid"] is True
