from unittest.mock import patch
from app.models import JobStatus, CertificateStatus


def test_individual_recipient_validation_failure_isolation(client):
    """
    Test that an invalid recipient email fails cleanly without preventing
    other valid recipients from generating successfully.
    The job completes with PARTIAL_SUCCESS.
    """
    payload = {
        "title": "Data Science Bootcamp",
        "issuer_name": "Aereo Data Lab",
        "recipients": [
            {"name": "Valid Recipient", "email": "valid.user@example.com"},
            {"name": "Invalid Recipient", "email": "not-an-email-at-all"}
        ]
    }

    create_resp = client.post("/api/v1/certificates/jobs", json=payload)
    assert create_resp.status_code == 202
    job_id = create_resp.json()["job_id"]

    status_resp = client.get(f"/api/v1/certificates/jobs/{job_id}")
    assert status_resp.status_code == 200

    data = status_resp.json()
    assert data["status"] == JobStatus.PARTIAL_SUCCESS
    assert data["total_count"] == 2
    assert data["processed_count"] == 2
    assert data["success_count"] == 1
    assert data["failed_count"] == 1

    certs = {c["recipient_name"]: c for c in data["certificates"]}
    
    # Valid user check
    assert certs["Valid Recipient"]["status"] == CertificateStatus.COMPLETED
    assert certs["Valid Recipient"]["download_url"] is not None

    # Invalid user check
    assert certs["Invalid Recipient"]["status"] == CertificateStatus.FAILED
    assert "Invalid email format" in certs["Invalid Recipient"]["error_message"]
    assert certs["Invalid Recipient"]["download_url"] is None


def test_generator_runtime_exception_isolation(client, monkeypatch):
    """
    Test that if one certificate triggers an unexpected runtime error during PDF generation,
    the remaining certificates are unaffected and generated successfully.
    """
    import app.services.job_processor as jp
    original_gen = jp.generate_certificate_pdf

    call_count = 0

    def mock_generator(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise RuntimeError("Simulated render glitch for recipient 1")
        return original_gen(*args, **kwargs)

    monkeypatch.setattr(jp, "generate_certificate_pdf", mock_generator)

    payload = {
        "title": "Quantum Computing 201",
        "issuer_name": "Aereo Quantum Group",
        "recipients": [
            {"name": "Recipient One", "email": "rec1@example.com"},
            {"name": "Recipient Two", "email": "rec2@example.com"}
        ]
    }

    create_resp = client.post("/api/v1/certificates/jobs", json=payload)
    job_id = create_resp.json()["job_id"]

    status_resp = client.get(f"/api/v1/certificates/jobs/{job_id}")
    data = status_resp.json()

    assert data["status"] == JobStatus.PARTIAL_SUCCESS
    assert data["success_count"] == 1
    assert data["failed_count"] == 1

    certs = {c["recipient_name"]: c for c in data["certificates"]}
    assert certs["Recipient One"]["status"] == CertificateStatus.FAILED
    assert "Simulated render glitch" in certs["Recipient One"]["error_message"]
    assert certs["Recipient Two"]["status"] == CertificateStatus.COMPLETED
