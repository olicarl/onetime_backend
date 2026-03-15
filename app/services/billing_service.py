import os
from datetime import datetime, date
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models import BillingSettings, Invoice, ChargingSession, Renter, BillingPeriodicity
from qrbill.bill import QRBill

INVOICES_DIR = "/data/invoices"

def ensure_invoices_dir():
    if not os.path.exists(INVOICES_DIR):
        os.makedirs(INVOICES_DIR, exist_ok=True)

def generate_invoice_pdf(invoice: Invoice, settings: BillingSettings) -> str:
    """Generate a Swiss QR Bill PDF for the invoice and return the file path."""
    ensure_invoices_dir()
    
    # Construct filename
    filename = f"invoice_{invoice.id}_{invoice.renter.name.replace(' ', '_')}_{invoice.period_start.strftime('%Y%m')}.svg"
    filepath = os.path.join(INVOICES_DIR, filename)
    pdf_filepath = filepath.replace(".svg", ".pdf")

    # Simple invoice details (In a real scenario, you'd use a templating engine like Jinja + Weasyprint for the full page, 
    # but here we generate the QR bill part)
    
    qr_bill = QRBill(
        account=settings.iban,
        creditor={
            "name": settings.company_name,
            "line1": settings.address.split(',')[0] if ',' in settings.address else settings.address,
            "line2": settings.address.split(',')[1].strip() if ',' in settings.address else "Switzerland",
            "country": "CH"
        },
        debtor={
            "name": invoice.renter.name,
            "line1": "Underground Parking",
            "line2": "Switzerland",
            "country": "CH"
        },
        amount=str(round(invoice.amount_due, 2)),
        currency="CHF",
        additional_information=f"Invoice {invoice.id} for charging sessions",
    )
    
    # Generate SVG
    qr_bill.as_svg(filepath)
    
    # Convert SVG to PDF using svglib and reportlab
    try:
        from svglib.svglib import svg2rlg
        from reportlab.graphics import renderPDF
        drawing = svg2rlg(filepath)
        renderPDF.drawToFile(drawing, pdf_filepath)
        # Optionally delete the svg
        if os.path.exists(filepath):
            os.remove(filepath)
        return pdf_filepath
    except Exception as e:
        print(f"Error converting SVG to PDF: {e}")
        return filepath # Return SVG path fallback


def calculate_and_generate_invoice(db: Session, renter: Renter, period_end_date: datetime) -> Optional[Invoice]:
    """Calculate due amount for unbilled sessions up to a date and generate an invoice."""
    settings = db.query(BillingSettings).first()
    if not settings:
        raise ValueError("Billing settings not configured")

    # Find unbilled sessions for this renter that ended before or on the period_end_date
    unbilled_sessions = db.query(ChargingSession).join(
        ChargingSession.token_rel
    ).filter(
        ChargingSession.token_rel.has(renter_id=renter.id),
        ChargingSession.invoice_id == None,
        ChargingSession.start_time <= period_end_date,
        ChargingSession.total_energy_kwh > 0
    ).all()

    if not unbilled_sessions:
        return None

    total_kwh = sum([session.total_energy_kwh for session in unbilled_sessions if session.total_energy_kwh])
    amount_due = total_kwh * settings.price_per_kwh

    if amount_due <= 0:
        return None

    # Determine period start from the earliest session
    period_start = min([session.start_time for session in unbilled_sessions])

    # Create Invoice record
    invoice = Invoice(
        renter_id=renter.id,
        period_start=period_start,
        period_end=period_end_date,
        amount_due=amount_due,
        is_paid=False
    )
    db.add(invoice)
    db.commit()
    db.refresh(invoice)

    # Link sessions
    for session in unbilled_sessions:
        session.invoice_id = invoice.id
    db.commit()

    # Generate PDF
    file_path = generate_invoice_pdf(invoice, settings)
    invoice.file_path = file_path
    db.commit()

    return invoice


def get_billing_settings(db: Session) -> BillingSettings:
    settings = db.query(BillingSettings).first()
    if not settings:
        settings = BillingSettings(
            company_name="My Parking Garage",
            iban="CH6209000000000000000",
            address="Parking Street 1, 1000 City",
            periodicity=BillingPeriodicity.Monthly,
            price_per_kwh=0.30
        )
        db.add(settings)
        db.commit()
        db.refresh(settings)
    return settings
