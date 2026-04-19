import os
from datetime import datetime, date
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models import BillingSettings, Invoice, ChargingSession, Renter, BillingPeriodicity
from qrbill.bill import QRBill

INVOICES_DIR = os.getenv("INVOICES_DIR", "/data/invoices")

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
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import mm
        from reportlab.platypus import Table, TableStyle
        from reportlab.lib import colors
        
        width, height = A4
        c = canvas.Canvas(pdf_filepath, pagesize=A4)
        
        # Draw header / Title
        c.setFont("Helvetica-Bold", 16)
        c.drawString(20*mm, height - 20*mm, "Invoice")
        
        c.setFont("Helvetica", 10)
        c.drawString(20*mm, height - 30*mm, f"Invoice #: {invoice.id}")
        c.drawString(20*mm, height - 35*mm, f"Period: {invoice.period_start.strftime('%d.%m.%Y')} to {invoice.period_end.strftime('%d.%m.%Y')}")
        
        # Company Info
        c.setFont("Helvetica-Bold", 10)
        c.drawString(120*mm, height - 20*mm, settings.company_name)
        c.setFont("Helvetica", 10)
        c.drawString(120*mm, height - 25*mm, settings.address)
        if settings.iban:
            c.drawString(120*mm, height - 30*mm, f"IBAN: {settings.iban}")
        
        # Debtor Info
        c.setFont("Helvetica-Bold", 10)
        c.drawString(20*mm, height - 50*mm, "Bill To:")
        c.setFont("Helvetica", 10)
        c.drawString(20*mm, height - 55*mm, invoice.renter.name)
        
        # Draw Sessions Table
        c.setFont("Helvetica-Bold", 12)
        c.drawString(20*mm, height - 75*mm, "Charging Sessions")
        
        data = [["Start Time", "End Time", "Energy (kWh)", "Cost (CHF)"]]
        for session in invoice.sessions:
            start_str = session.start_time.strftime('%d.%m.%Y %H:%M')
            end_str = session.end_time.strftime('%d.%m.%Y %H:%M') if session.end_time else "N/A"
            kwh = round(session.total_energy_kwh or 0, 2)
            cost = round(kwh * settings.price_per_kwh, 2)
            data.append([start_str, end_str, f"{kwh:.2f}", f"{cost:.2f}"])
            
        # Total row
        data.append(["", "", "Total Amount Due:", f"{round(invoice.amount_due, 2):.2f} CHF"])
        
        # Create table
        table = Table(data, colWidths=[45*mm, 45*mm, 35*mm, 35*mm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#f3f4f6")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (2, 0), (3, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -2), 0.5, colors.HexColor("#e5e7eb")),
            ('FONTNAME', (2, -1), (3, -1), 'Helvetica-Bold'),
            ('LINEABOVE', (2, -1), (3, -1), 1, colors.black),
        ]))
        
        w, h = table.wrapOn(c, width, height)
        # Position it below the "Charging Sessions" title
        table.drawOn(c, 20*mm, height - 80*mm - h)
        
        # Load SVG
        drawing = svg2rlg(filepath)
        # Draw SVG at bottom left (0, 0)
        # The QR Bill is 210mm x 105mm, exactly the width of A4 and the bottom 1/3 of the page
        renderPDF.draw(drawing, c, 0, 0)
        
        c.save()
        
        # Optionally delete the svg
        if os.path.exists(filepath):
            os.remove(filepath)
        return pdf_filepath
    except Exception as e:
        import traceback
        traceback.print_exc()
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
