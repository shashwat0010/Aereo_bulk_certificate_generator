import os
from pathlib import Path
from app.services.certificate_generator import generate_certificate_pdf
from app.config import CERTIFICATES_DIR


def test_certificate_pdf_generation_file_integrity():
    """Unit test for PDF generation verifying file creation and PDF binary signature."""
    test_cert_id = "test-pdf-generation-unit"
    test_code = "CERT-UNITTEST123"
    
    expected_path = CERTIFICATES_DIR / f"{test_cert_id}.pdf"
    if expected_path.exists():
        expected_path.unlink()

    pdf_path = generate_certificate_pdf(
        certificate_id=test_cert_id,
        certificate_code=test_code,
        recipient_name="Samantha Taylor",
        title="Advanced Robotics Engineering",
        description="Completed specialized training in robotic manipulation and autonomous systems.",
        issuer_name="Robotics Council",
        issue_date="October 6, 2026"
    )

    assert Path(pdf_path).exists()
    assert os.path.getsize(pdf_path) > 1000  # PDF should be non-trivial size

    # Verify standard PDF magic header
    with open(pdf_path, "rb") as f:
        header = f.read(5)
        assert header == b"%PDF-"

    # Cleanup
    if expected_path.exists():
        expected_path.unlink()
