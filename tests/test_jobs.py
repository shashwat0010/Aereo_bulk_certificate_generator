import time
from app.models import JobStatus


def test_create_generation_job_success(client):
    """Test submitting a valid bulk certificate generation request."""
    payload = {
        "title": "Machine Learning Fundamentals",
        "description": "Comprehensive course on deep learning and AI models.",
        "issuer_name": "Aereo Tech Institute",
        "issue_date": "October 6, 2026",
        "recipients": [
            {"name": "Alice Smith", "email": "alice@example.com"},
            {"name": "Bob Jones", "email": "bob@example.com"}
        ]
    }

    response = client.post("/api/v1/certificates/jobs", json=payload)
    assert response.status_code == 202

    data = response.json()
    assert "job_id" in data
    assert data["title"] == payload["title"]
    assert data["total_count"] == 2
    assert data["issuer_name"] == payload["issuer_name"]


def test_get_job_status_and_progress(client):
    """Test retrieving job status, checking progress counters and certificates."""
    payload = {
        "title": "Python Architecture",
        "description": "Backend design and scalability.",
        "issuer_name": "Aereo Engineering",
        "recipients": [
            {"name": "Charlie Brown", "email": "charlie@example.com"}
        ]
    }

    create_resp = client.post("/api/v1/certificates/jobs", json=payload)
    job_id = create_resp.json()["job_id"]

    status_resp = client.get(f"/api/v1/certificates/jobs/{job_id}")
    assert status_resp.status_code == 200

    data = status_resp.json()
    assert data["job_id"] == job_id
    assert data["status"] in (JobStatus.COMPLETED, JobStatus.PROCESSING)
    assert data["total_count"] == 1
    assert data["success_count"] == 1
    assert data["failed_count"] == 0
    assert len(data["certificates"]) == 1
    assert data["certificates"][0]["recipient_name"] == "Charlie Brown"
    assert data["certificates"][0]["status"] == "COMPLETED"
    assert data["certificates"][0]["download_url"] is not None
    assert data["zip_download_url"] is not None


def test_list_jobs(client):
    """Test listing all jobs."""
    response = client.get("/api/v1/certificates/jobs")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
