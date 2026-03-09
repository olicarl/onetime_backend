from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from pydantic import BaseModel
from typing import List, Optional
import os

from app.database import get_db
from app.models import BillingSettings, Invoice, Renter, BillingPeriodicity
from app.services.billing_service import get_billing_settings, calculate_and_generate_invoice
from fastapi.responses import FileResponse

router = APIRouter(prefix="/billing", tags=["billing"])

class BillingSettingsSchema(BaseModel):
    company_name: str
    iban: str
    address: str
    periodicity: BillingPeriodicity
    price_per_kwh: float

    class Config:
        from_attributes = True

class InvoiceSchema(BaseModel):
    id: int
    renter_id: int
    period_start: datetime
    period_end: datetime
    amount_due: float
    is_paid: bool
    created_at: datetime
    renter_name: str

    class Config:
        from_attributes = True

class GenerateInvoiceRequest(BaseModel):
    renter_id: int
    end_date: datetime


@router.get("/settings", response_model=BillingSettingsSchema)
def api_get_billing_settings(db: Session = Depends(get_db)):
    settings = get_billing_settings(db)
    return settings

@router.put("/settings", response_model=BillingSettingsSchema)
def api_update_billing_settings(settings_data: BillingSettingsSchema, db: Session = Depends(get_db)):
    settings = get_billing_settings(db)
    settings.company_name = settings_data.company_name
    settings.iban = settings_data.iban
    settings.address = settings_data.address
    settings.periodicity = settings_data.periodicity
    settings.price_per_kwh = settings_data.price_per_kwh
    db.commit()
    db.refresh(settings)
    return settings


@router.get("/invoices", response_model=List[InvoiceSchema])
def list_invoices(db: Session = Depends(get_db)):
    invoices = db.query(Invoice).all()
    result = []
    for inv in invoices:
        result.append(InvoiceSchema(
            id=inv.id,
            renter_id=inv.renter.id,
            period_start=inv.period_start,
            period_end=inv.period_end,
            amount_due=inv.amount_due,
            is_paid=inv.is_paid,
            created_at=inv.created_at,
            renter_name=inv.renter.name if inv.renter else "Unknown"
        ))
    return result

@router.post("/invoices/generate")
def generate_manual_invoice(req: GenerateInvoiceRequest, db: Session = Depends(get_db)):
    renter = db.query(Renter).filter(Renter.id == req.renter_id).first()
    if not renter:
        raise HTTPException(status_code=404, detail="Renter not found")
    
    try:
        invoice = calculate_and_generate_invoice(db, renter, req.end_date)
        if not invoice:
            return {"message": "No unbilled sessions found for this renter in the given period.", "invoice_id": None}
        return {"message": "Invoice generated successfully", "invoice_id": invoice.id}
    except ValueError as e:
         raise HTTPException(status_code=400, detail=str(e))

@router.post("/invoices/{invoice_id}/mark-paid")
def mark_invoice_paid(invoice_id: int, db: Session = Depends(get_db)):
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    invoice.is_paid = not invoice.is_paid # Toggle
    db.commit()
    return {"message": f"Invoice marked as {'paid' if invoice.is_paid else 'unpaid'}", "is_paid": invoice.is_paid}

@router.get("/invoices/{invoice_id}/pdf")
def get_invoice_pdf(invoice_id: int, db: Session = Depends(get_db)):
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    if not invoice.file_path or not os.path.exists(invoice.file_path):
        raise HTTPException(status_code=404, detail="PDF not found on disk")
    
    # Check if the path ends with .pdf, if not send the svg
    media_type = "application/pdf" if invoice.file_path.endswith(".pdf") else "image/svg+xml"
    filename = os.path.basename(invoice.file_path)

    return FileResponse(
        path=invoice.file_path,
        media_type=media_type,
        filename=filename
    )
