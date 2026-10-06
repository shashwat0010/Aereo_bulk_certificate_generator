# Bulk Certificate Generator API & Service

A robust, production-grade backend API built with **FastAPI**, **SQLAlchemy**, and **ReportLab** that accepts high-volume certificate generation requests, processes them asynchronously, tracks real-time generation progress, provides resilient partial-failure isolation, and enables instant single or bulk ZIP downloads.

Includes an interactive **Web Dashboard**, comprehensive **Pytest test suite**, and an **Autonomous QA Agent** for end-to-end sanity and stress testing.

---

## 🌟 Key Features

- **High-Volume Bulk Processing**: Submit hundreds or thousands of recipients in a single API call; background workers process generation asynchronously without blocking HTTP threads.
- **Fault-Tolerant Error Isolation**: An invalid email address or generation failure for an individual recipient **never** crashes or halts the rest of the batch. The system marks individual certificates as `FAILED` with explicit error causes and marks the overall job as `PARTIAL_SUCCESS`.
- **Vector PDF Certificate Engine**: Built with ReportLab, producing high-resolution, landscape A4 certificates styled with custom typography, metallic gold borders, dynamic recipient names, issue dates, and embedded QR codes.
- **Public Verification System**: Each certificate generates a unique verification code (`CERT-XXXXXXXXXX`) and scannable QR code that resolves to `/api/v1/certificates/verify/{code}`.
- **Bulk Download & Archiving**: Download single PDF certificates on demand or stream the entire job bundle as an in-memory ZIP archive (`/download-zip`).
- **Real-Time Progress Tracking**: Live polling endpoints return processing counters (`processed_count`, `success_count`, `failed_count`), percentage completion, and per-recipient status.
- **Interactive Web UI**: Built-in dashboard accessible at `http://localhost:8000/` to test jobs, load sample batches, inspect live progress, and preview PDFs in-browser.
- **Autonomous QA Agent**: Included testing agent script (`scripts/qa_agent.py`) that benchmarks generation throughput and verifies end-to-end data integrity.

---

## 🏗️ Architecture & Design Decisions

### 1. Synchronous API vs. Asynchronous Background Execution
- **Decision**: The API accepts jobs via `POST /api/v1/certificates/jobs`, validates the payload structure, immediately writes records to the relational database in `PENDING` status, and responds with `HTTP 202 Accepted` within milliseconds.
- **Reasoning**: Generating PDFs is CPU and I/O intensive. Blocking an HTTP request while generating hundreds of PDF certificates would cause request timeouts, exhaust server worker threads, and degrade client experience. Background task dispatch ensures fast API response times while jobs execute safely in the background.

### 2. Database & Concurrency Strategy (SQLite with WAL)
- **Decision**: Uses **SQLAlchemy 2.0** with **SQLite** in Write-Ahead Logging (`PRAGMA journal_mode=WAL`) mode.
- **Reasoning**: WAL allows concurrent readers while background workers write progress updates without database locking contention. The system uses a clean relational schema (`Job` $\leftrightarrow$ `Certificate`) and is configurable to PostgreSQL via the `DATABASE_URL` environment variable.

### 3. Failure & Validation Isolation
- **Decision**: Recipient validation and rendering execute inside an isolated per-recipient try/catch block within `app/services/job_processor.py`.
- **Reasoning**: If 1 recipient out of 100 has a malformed email or causes a rendering error, the other 99 certificates are generated and delivered. The job concludes with `PARTIAL_SUCCESS` and records granular error messages for debugging.

---

## 📁 Project Structure

```
Aereo_assignment/
├── app/
│   ├── __init__.py
│   ├── main.py                  # FastAPI application entrypoint & lifespan
│   ├── config.py                # Configuration, paths, batch limits
│   ├── database.py              # SQLAlchemy engine, session maker, WAL pragma
│   ├── models.py                # Database models (Job, Certificate)
│   ├── schemas.py               # Pydantic schemas (Request, Response, Status)
│   ├── services/
│   │   ├── __init__.py
│   │   ├── certificate_generator.py # ReportLab PDF & QR code engine
│   │   └── job_processor.py     # Background worker orchestrating generation & error handling
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes.py            # API endpoints (/jobs, /certificates, /verify)
│   │   └── web.py               # Web dashboard router
│   └── static/
│       ├── index.html           # Interactive web dashboard
│       ├── style.css            # Obsidian & Gold modern theme
│       └── app.js               # Frontend polling, submission & preview logic
├── storage/
│   └── certificates/            # Directory where generated PDF certificates reside
├── data/
│   └── certificates.db          # Relational SQLite database file
├── tests/
│   ├── __init__.py
│   ├── conftest.py              # Test database and client fixtures
│   ├── test_jobs.py             # Job creation and status tests
│   ├── test_validation.py       # Input validation tests
│   ├── test_generator.py        # PDF generator unit tests
│   ├── test_failure_handling.py # Partial failure resilience tests
│   └── test_retrieval.py        # Certificate download & zip tests
├── scripts/
│   └── qa_agent.py              # Autonomous QA testing & benchmark agent
├── requirements.txt
├── pytest.ini
└── README.md
```

---

## 🚀 Setup & Installation

### Prerequisites
- Python 3.10+ (Tested on Python 3.12)
- pip

### 1. Clone & Navigate to Repository
```bash
git clone <repository_url>
cd Aereo_assignment
```

### 2. (Optional) Create Virtual Environment
```bash
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Linux / macOS:
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

---

## 🏃 Running the Application

### Start the FastAPI Server
```bash
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

The server starts at `http://127.0.0.1:8000`.

### Access Interfaces
- **Interactive Web Dashboard**: [http://localhost:8000/](http://localhost:8000/)
- **Swagger / OpenAPI Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc Interactive Reference**: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **Health Check**: [http://localhost:8000/health](http://localhost:8000/health)

---

## 🧪 Running Tests & Autonomous QA Agent

### 1. Run Automated Test Suite (Pytest)
```bash
python -m pytest -v
```
All 15 tests cover:
1. Job creation (`test_create_generation_job_success`)
2. Job polling and status (`test_get_job_status_and_progress`, `test_list_jobs`)
3. Input validation: empty lists, missing fields, whitespace (`test_validation_*`)
4. PDF generation binary headers and file creation (`test_certificate_pdf_generation_file_integrity`)
5. Partial failure isolation & error recording (`test_individual_recipient_validation_failure_isolation`)
6. Generator exception tolerance (`test_generator_runtime_exception_isolation`)
7. Individual PDF download & inline preview (`test_download_individual_certificate`, `test_preview_individual_certificate`)
8. Bulk ZIP archive packaging (`test_download_job_certificates_zip`)
9. Public certificate verification (`test_certificate_verification`)

### 2. Run Autonomous QA Agent
To execute the autonomous diagnostic battery (which stress tests batch generation throughput, inspects PDF byte signatures, verifies fault-tolerance chaos tests, and generates a structured `qa_report.json`):
```bash
python scripts/qa_agent.py
```

Sample output:
```text
========================================================================
  🤖 BULK CERTIFICATE GENERATOR - AUTONOMOUS QA AGENT
  Target: Bulk Certificate Generator v1.0.0 | Python: 3.12.6
========================================================================

[Scenario 1] System Environment & Health Diagnostic
  [PASS] Health Endpoint Check (24.9ms) - API reported healthy status
  [PASS] Storage & Data Dir Integrity (0.2ms) - Certificates Dir: ...

[Scenario 2] Bulk Generation & Throughput Benchmark (20 recipients)
  [PASS] Batch Job Submission (517.3ms) - Job accepted with UUID ...
  [PASS] Bulk Batch Execution (20 certs) (523.2ms) - Completed (~38.2 certs/sec).

[Scenario 3] Fault Tolerance & Partial Failure Isolation
  [PASS] Partial Failure Handling (62.9ms) - Job correctly flagged PARTIAL_SUCCESS
  [PASS] Error Message Granularity (1.0ms) - Recipient error accurately captured

[Scenario 4] PDF Binary & Format Integrity Audit
  [PASS] PDF Magic Header & MIME Verification (11.2ms) - Verified %PDF- header

[Scenario 5] ZIP Archive Bundle Packaging Verification
  [PASS] ZIP Bundle Integrity (90.5ms) - Successfully unzipped 20 certificates

[Scenario 6] Certificate Authenticity Verification Endpoint
  [PASS] Authentic Certificate Verification (7.5ms)
  [PASS] Fraudulent / Invalid Code Rejection (4.7ms)
========================================================================
  📊 QA AGENT EXECUTION SUMMARY: 10 Passed, 0 Failed, ~38.2 certs/sec
========================================================================
```

---

## 📡 API Usage Guide

### 1. Submit a Bulk Certificate Generation Job
- **Endpoint**: `POST /api/v1/certificates/jobs`
- **Status**: `202 Accepted`

#### Example Request:
```bash
curl -X POST "http://localhost:8000/api/v1/certificates/jobs" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Autonomous Drone Engineering Masterclass",
    "issuer_name": "Aereo Flight Academy",
    "issue_date": "October 6, 2026",
    "description": "For demonstrating mastery in UAV avionics and autonomous flight systems.",
    "recipients": [
      {
        "name": "Sarah Connor",
        "email": "sarah.connor@example.com"
      },
      {
        "name": "Alex Murphy",
        "email": "alex.murphy@example.com"
      }
    ]
  }'
```

#### Example Response:
```json
{
  "job_id": "a931dc12-4011-4a39-9d95-8ec66d7adbc7",
  "title": "Autonomous Drone Engineering Masterclass",
  "description": "For demonstrating mastery in UAV avionics and autonomous flight systems.",
  "issuer_name": "Aereo Flight Academy",
  "issue_date": "October 6, 2026",
  "status": "PENDING",
  "total_count": 2,
  "processed_count": 0,
  "success_count": 0,
  "failed_count": 0,
  "created_at": "2026-10-06T15:50:00.000000Z"
}
```

---

### 2. Check Job Progress & Retrieve Certificates
- **Endpoint**: `GET /api/v1/certificates/jobs/{job_id}`
- **Status**: `200 OK`

#### Example Request:
```bash
curl -X GET "http://localhost:8000/api/v1/certificates/jobs/a931dc12-4011-4a39-9d95-8ec66d7adbc7"
```

#### Example Response:
```json
{
  "job_id": "a931dc12-4011-4a39-9d95-8ec66d7adbc7",
  "title": "Autonomous Drone Engineering Masterclass",
  "status": "COMPLETED",
  "total_count": 2,
  "processed_count": 2,
  "success_count": 2,
  "failed_count": 0,
  "zip_download_url": "/api/v1/certificates/jobs/a931dc12-4011-4a39-9d95-8ec66d7adbc7/download-zip",
  "certificates": [
    {
      "id": "e2f1ab44-22b0-466a-bc07-2c97486f0301",
      "recipient_name": "Sarah Connor",
      "recipient_email": "sarah.connor@example.com",
      "certificate_code": "CERT-8D1F20AB43",
      "status": "COMPLETED",
      "error_message": null,
      "download_url": "/api/v1/certificates/e2f1ab44-22b0-466a-bc07-2c97486f0301/download"
    },
    {
      "id": "b781ce29-91a1-432d-86ea-1fca718b5324",
      "recipient_name": "Alex Murphy",
      "recipient_email": "alex.murphy@example.com",
      "certificate_code": "CERT-4A99EFB120",
      "status": "COMPLETED",
      "error_message": null,
      "download_url": "/api/v1/certificates/b781ce29-91a1-432d-86ea-1fca718b5324/download"
    }
  ]
}
```

---

### 3. Download an Individual Certificate PDF
- **Endpoint**: `GET /api/v1/certificates/{certificate_id}/download`
- **Status**: `200 OK` (`application/pdf`)

```bash
curl -O -J "http://localhost:8000/api/v1/certificates/e2f1ab44-22b0-466a-bc07-2c97486f0301/download"
```

---

### 4. Download All Certificates as a ZIP Bundle
- **Endpoint**: `GET /api/v1/certificates/jobs/{job_id}/download-zip`
- **Status**: `200 OK` (`application/zip`)

```bash
curl -O -J "http://localhost:8000/api/v1/certificates/jobs/a931dc12-4011-4a39-9d95-8ec66d7adbc7/download-zip"
```

---

### 5. Verify Certificate Authenticity
- **Endpoint**: `GET /api/v1/certificates/verify/{certificate_code}`
- **Status**: `200 OK`

```bash
curl -X GET "http://localhost:8000/api/v1/certificates/verify/CERT-8D1F20AB43"
```

#### Example Response:
```json
{
  "valid": true,
  "certificate_code": "CERT-8D1F20AB43",
  "recipient_name": "Sarah Connor",
  "recipient_email": "sarah.connor@example.com",
  "title": "Autonomous Drone Engineering Masterclass",
  "issuer_name": "Aereo Flight Academy",
  "issue_date": "October 6, 2026",
  "issued_at": "October 06, 2026",
  "message": "Certificate is authentic and officially issued."
}
```

---

## 🛡️ Validation & Failure Handling Details

| Condition | System Reaction | Job Status Outcome |
| :--- | :--- | :--- |
| Empty recipients list / Missing title | Rejection at API boundary with `HTTP 422 Unprocessable Entity` | Request aborted |
| All recipients valid | Asynchronously generates all PDFs | `COMPLETED` (`success_count == total_count`) |
| 1 or more recipients have invalid emails or rendering faults | Faulty item flagged `FAILED` with explicit error message; remaining valid items generated successfully | `PARTIAL_SUCCESS` (`success_count > 0`, `failed_count > 0`) |
| All items failed | All items flagged `FAILED` | `FAILED` (`success_count == 0`) |
