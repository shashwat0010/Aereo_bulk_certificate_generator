import os
from pathlib import Path
from reportlab.lib.pagesizes import letter, landscape, A4
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.graphics.shapes import Drawing, Rect
from reportlab.graphics.barcode import qr
from app.config import CERTIFICATES_DIR, BASE_URL


def generate_certificate_pdf(
    certificate_id: str,
    certificate_code: str,
    recipient_name: str,
    title: str,
    description: str,
    issuer_name: str,
    issue_date: str,
    output_path: str = None
) -> str:
    """
    Generates a high-quality landscape PDF certificate using ReportLab.
    Returns the absolute path to the generated PDF.
    """
    if not output_path:
        output_path = str(CERTIFICATES_DIR / f"{certificate_id}.pdf")

    # Use landscape A4 (841.89 x 595.27 points)
    page_width, page_height = landscape(A4)
    c = canvas.Canvas(output_path, pagesize=(page_width, page_height))
    c.setTitle(f"Certificate - {recipient_name}")

    # Palette
    c_navy = colors.HexColor("#0B132B")
    c_gold = colors.HexColor("#C59B27")
    c_dark_gold = colors.HexColor("#9A7B1C")
    c_light_bg = colors.HexColor("#FAF9F5")
    c_text_dark = colors.HexColor("#1C2541")
    c_text_muted = colors.HexColor("#475569")

    # 1. Background Fill
    c.setFillColor(c_light_bg)
    c.rect(0, 0, page_width, page_height, fill=1, stroke=0)

    # 2. Outer Deep Navy Border
    c.setStrokeColor(c_navy)
    c.setLineWidth(6)
    c.rect(20, 20, page_width - 40, page_height - 40, fill=0, stroke=1)

    # 3. Inner Gold Border
    c.setStrokeColor(c_gold)
    c.setLineWidth(2)
    c.rect(28, 28, page_width - 56, page_height - 56, fill=0, stroke=1)

    # 4. Corner Ornaments (Gold Triangles/Squares)
    corner_size = 14
    for x, y in [
        (28, 28),
        (page_width - 28 - corner_size, 28),
        (28, page_height - 28 - corner_size),
        (page_width - 28 - corner_size, page_height - 28 - corner_size)
    ]:
        c.setFillColor(c_gold)
        c.rect(x, y, corner_size, corner_size, fill=1, stroke=0)

    # 5. Header / Badge
    c.setFillColor(c_gold)
    c.setFont("Helvetica-Bold", 13)
    c.drawCentredString(page_width / 2, page_height - 75, "★ ★ ★   OFFICIAL RECOGNITION   ★ ★ ★")

    # 6. Main Certificate Title
    c.setFillColor(c_navy)
    c.setFont("Helvetica-Bold", 32)
    c.drawCentredString(page_width / 2, page_height - 118, "CERTIFICATE OF ACHIEVEMENT")

    # 7. Presentation Subtitle
    c.setFillColor(c_text_muted)
    c.setFont("Helvetica", 13)
    c.drawCentredString(page_width / 2, page_height - 150, "THIS CERTIFICATE IS PROUDLY PRESENTED TO")

    # 8. Recipient Name
    c.setFillColor(c_navy)
    c.setFont("Helvetica-Bold", 34)
    c.drawCentredString(page_width / 2, page_height - 210, recipient_name)

    # Accent underline beneath recipient name
    name_width = min(c.stringWidth(recipient_name, "Helvetica-Bold", 34) + 60, 480)
    c.setStrokeColor(c_gold)
    c.setLineWidth(2)
    c.line((page_width - name_width) / 2, page_height - 222, (page_width + name_width) / 2, page_height - 222)

    # 9. Context & Course Title
    c.setFillColor(c_text_muted)
    c.setFont("Helvetica", 12)
    c.drawCentredString(page_width / 2, page_height - 255, "in recognition of successfully completing all requirements for")

    c.setFillColor(c_navy)
    c.setFont("Helvetica-Bold", 20)
    c.drawCentredString(page_width / 2, page_height - 285, title)

    # Description (with safe length truncation/wrap)
    if description:
        desc_text = description if len(description) <= 120 else description[:117] + "..."
        c.setFillColor(c_text_muted)
        c.setFont("Helvetica-Oblique", 11)
        c.drawCentredString(page_width / 2, page_height - 315, desc_text)

    # 10. Footer Section (3 columns: Date, QR Code + Verification, Signature & Issuer)
    y_footer_line = 110

    # Column 1: Date of Issue
    c.setFillColor(c_text_dark)
    c.setFont("Helvetica-Bold", 12)
    c.drawCentredString(160, y_footer_line + 20, issue_date)
    c.setStrokeColor(c_navy)
    c.setLineWidth(1)
    c.line(80, y_footer_line + 12, 240, y_footer_line + 12)
    c.setFillColor(c_text_muted)
    c.setFont("Helvetica", 10)
    c.drawCentredString(160, y_footer_line - 5, "DATE OF ISSUANCE")

    # Column 2: Center QR Code and Unique Verification Code
    verify_url = f"{BASE_URL}/api/v1/certificates/verify/{certificate_code}"
    try:
        qr_code = qr.QrCodeWidget(verify_url)
        qr_code.barWidth = 55
        qr_code.barHeight = 55
        qr_code.qrVersion = 1
        d = Drawing(55, 55)
        d.add(qr_code)
        # Render QR code drawing onto canvas
        d.drawOn(c, (page_width / 2) - 27.5, y_footer_line - 15)
    except Exception:
        # Fallback if QR rendering encounters issue
        c.setFillColor(c_gold)
        c.rect((page_width / 2) - 25, y_footer_line - 10, 50, 50, fill=0, stroke=1)

    c.setFillColor(c_text_muted)
    c.setFont("Helvetica-Bold", 9)
    c.drawCentredString(page_width / 2, y_footer_line - 30, f"ID: {certificate_code}")
    c.setFont("Helvetica", 7.5)
    c.drawCentredString(page_width / 2, y_footer_line - 42, "Scan to verify authenticity")

    # Column 3: Issuer Signature
    c.setFillColor(c_navy)
    c.setFont("Times-BoldItalic", 16)
    c.drawCentredString(page_width - 160, y_footer_line + 22, issuer_name)
    c.setStrokeColor(c_navy)
    c.setLineWidth(1)
    c.line(page_width - 240, y_footer_line + 12, page_width - 80, y_footer_line + 12)
    c.setFillColor(c_text_muted)
    c.setFont("Helvetica", 10)
    c.drawCentredString(page_width - 160, y_footer_line - 5, "AUTHORIZED SIGNATURE")

    # Finalize Page
    c.showPage()
    c.save()

    return output_path
