import io
import zipfile
from app.models import CertificateStatus


def test_download_individual_certificate(client):
    """Test downloading a completed certificate returns PDF with correct headers."""
    payload = {
        "title": "DevOps Engineering",
        "issuer_name": "Aereo Cloud Ops",
        "recipients": [{"name": "David Miller", "email": "david@example.com"}]
    }

    create_resp = client.post("/api/v1/certificates/jobs", json=payload)
    job_id = create_resp.json()["job_id"]

    status_resp = client.get(f"/api/v1/certificates/jobs/{job_id}")
    cert_id = status_resp.json()["certificates"][0]["id"]

    # Download PDF
    dl_resp = client.get(f"/api/v1/certificates/{cert_id}/download")
    assert dl_resp.status_code == 200
    assert dl_resp.headers["content-type"] == "application/pdf"
    assert "attachment" in dl_resp.headers["content-disposition"]
    assert dl_resp.content.startswith(b"%PDF-")


def test_preview_individual_certificate(client):
    """Test inline preview of certificate."""
    payload = {
        "title": "DevOps Engineering",
        "issuer_name": "Aereo Cloud Ops",
        "recipients": [{"name": "Eva Green", "email": "eva@example.com"}]
    }

    create_resp = client.post("/api/v1/certificates/jobs", json=payload)
    job_id = create_resp.json()["job_id"]

    status_resp = client.get(f"/api/v1/certificates/jobs/{job_id}")
    cert_id = status_resp.json()["certificates"][0]["id"]

    preview_resp = client.get(f"/api/v1/certificates/{cert_id}/preview")
    assert preview_resp.status_code == 200
    assert preview_resp.headers["content-type"] == "application/pdf"
    assert "inline" in preview_resp.headers["content-disposition"]


def test_download_job_certificates_zip(client):
    """Test downloading all completed certificates in a single ZIP bundle."""
    payload = {
        "title": "Cybersecurity Specialist",
        "issuer_name": "Aereo Security",
        "recipients": [
            {"name": "Frank White", "email": "frank@example.com"},
            {"name": "Grace Hopper", "email": "grace@example.com"}
        ]
    }

    create_resp = client.post("/api/v1/certificates/jobs", json=payload)
    job_id = create_resp.json()["job_id"]

    zip_resp = client.get(f"/api/v1/certificates/jobs/{job_id}/download-zip")
    assert zip_resp.status_code == 200
    assert zip_resp.headers["content-type"] == "application/zip"
    assert "attachment" in zip_resp.headers["content-disposition"]

    # Verify zip content
    zip_buf = io.BytesIO(zip_resp.content)
    with zipfile.ZipFile(zip_buf, "r") as zf:
        namelist = zf.namelist()
        assert len(namelist) == 2
        for name in namelist:
            assert name.endswith(".pdf")
            data = zf.read(name)
            assert data.startswith(b"%PDF-")


def test_certificate_verification(client):
    """Test public certificate verification endpoint."""
    payload = {
        "title": "AI Ethics",
        "issuer_name": "Aereo Ethics Board",
        "recipients": [{"name": "Helen Troy", "email": "helen@example.com"}]
    }

    create_resp = client.post("/api/v1/certificates/jobs", json=payload)
    job_id = create_resp.json()["job_id"]

    status_resp = client.get(f"/api/v1/certificates/jobs/{job_id}")
    cert_code = status_resp.json()["certificates"][0]["certificate_code"]

    # 1. Valid code check
    verify_resp = client.get(f"/api/v1/certificates/verify/{cert_code}")
    assert verify_resp.status_code == 200
    v_data = verify_resp.json()
    assert v_data["valid"] is True
    assert v_data["recipient_name"] == "Helen Troy"
    assert v_data["title"] == "AI Ethics"
    assert v_data["issuer_name"] == "Aereo Ethics Board"

    # 2. Invalid code check
    bad_resp = client.get("/api/v1/certificates/verify/CERT-INVALID999")
    assert bad_resp.status_code == 200
    b_data = bad_resp.json()
    assert b_data["valid"] is False
