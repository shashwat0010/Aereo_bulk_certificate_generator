def test_validation_empty_recipients(client):
    """Test creating a job with empty recipients list returns 422."""
    payload = {
        "title": "Cloud Computing 101",
        "issuer_name": "Aereo Cloud",
        "recipients": []
    }
    response = client.post("/api/v1/certificates/jobs", json=payload)
    assert response.status_code == 422


def test_validation_missing_required_fields(client):
    """Test creating a job without title or issuer_name fails."""
    # Missing title
    payload_no_title = {
        "issuer_name": "Aereo Cloud",
        "recipients": [{"name": "John Doe", "email": "john@example.com"}]
    }
    resp1 = client.post("/api/v1/certificates/jobs", json=payload_no_title)
    assert resp1.status_code == 422

    # Missing issuer_name
    payload_no_issuer = {
        "title": "Cloud Computing",
        "recipients": [{"name": "John Doe", "email": "john@example.com"}]
    }
    resp2 = client.post("/api/v1/certificates/jobs", json=payload_no_issuer)
    assert resp2.status_code == 422


def test_validation_blank_whitespace_fields(client):
    """Test providing whitespace only in required fields is rejected."""
    payload = {
        "title": "   ",
        "issuer_name": "Aereo Cloud",
        "recipients": [{"name": "John Doe", "email": "john@example.com"}]
    }
    response = client.post("/api/v1/certificates/jobs", json=payload)
    assert response.status_code == 422


def test_validation_blank_recipient_name(client):
    """Test providing recipient with blank name is rejected."""
    payload = {
        "title": "Cloud Computing",
        "issuer_name": "Aereo Cloud",
        "recipients": [{"name": "   ", "email": "john@example.com"}]
    }
    response = client.post("/api/v1/certificates/jobs", json=payload)
    assert response.status_code == 422


def test_job_not_found(client):
    """Test querying non-existent job ID returns 404."""
    response = client.get("/api/v1/certificates/jobs/non-existent-uuid-123")
    assert response.status_code == 404
