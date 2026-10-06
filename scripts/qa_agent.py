#!/usr/bin/env python
"""
Autonomous QA and Sanity Testing Agent for Bulk Certificate Generator.
Executes an end-to-end diagnostic battery covering:
  - System Health & Configuration Diagnostics
  - Large-Batch Bulk Generation & Throughput Benchmarking
  - Error Isolation & Fault Tolerance (Chaos Testing)
  - PDF Binary Verification & Integrity Audit
  - ZIP Bundle Packaging Inspection
  - Cryptographic / Verification Code Resolution
Outputs a detailed QA diagnostic report in terminal and saves 'qa_report.json'.
"""

import sys
import time
import json
import io
import zipfile
from pathlib import Path
from datetime import datetime

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

# Ensure utf-8 stdout for Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


from fastapi.testclient import TestClient
from app.main import app
from app.config import CERTIFICATES_DIR, DATA_DIR, APP_NAME, APP_VERSION


class Colors:
    HEADER = "\033[95m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BOLD = "\033[1m"
    RESET = "\033[0m"


class QAAgent:
    def __init__(self):
        self.client = TestClient(app)
        self.report = {
            "timestamp": datetime.now().isoformat(),
            "target_app": f"{APP_NAME} v{APP_VERSION}",
            "tests_run": 0,
            "tests_passed": 0,
            "tests_failed": 0,
            "scenarios": [],
            "performance_metrics": {},
        }

    def log(self, msg: str, color: str = Colors.RESET):
        print(f"{color}{msg}{Colors.RESET}")

    def banner(self):
        self.log("=" * 72, Colors.CYAN)
        self.log(f"  🤖 BULK CERTIFICATE GENERATOR - AUTONOMOUS QA AGENT", Colors.BOLD + Colors.CYAN)
        self.log(f"  Target: {APP_NAME} v{APP_VERSION} | Python: {sys.version.split()[0]}", Colors.BLUE)
        self.log("=" * 72, Colors.CYAN)

    def record_scenario(self, name: str, passed: bool, details: str, duration_ms: float):
        self.report["tests_run"] += 1
        if passed:
            self.report["tests_passed"] += 1
            self.log(f"  [PASS] {name} ({duration_ms:.1f}ms) - {details}", Colors.GREEN)
        else:
            self.report["tests_failed"] += 1
            self.log(f"  [FAIL] {name} ({duration_ms:.1f}ms) - {details}", Colors.RED)

        self.report["scenarios"].append({
            "name": name,
            "passed": passed,
            "details": details,
            "duration_ms": duration_ms
        })

    def run_all(self):
        self.banner()
        t_start = time.perf_counter()

        self.test_health_and_env()
        self.test_bulk_generation_throughput(count=20)
        self.test_fault_tolerance_and_error_isolation()
        self.test_pdf_binary_integrity()
        self.test_zip_archive_integrity()
        self.test_verification_resolution()

        total_time = (time.perf_counter() - t_start) * 1000
        self.report["total_execution_ms"] = round(total_time, 2)

        self.print_summary()
        self.save_report()

    def test_health_and_env(self):
        self.log("\n[Scenario 1] System Environment & Health Diagnostic", Colors.BOLD)
        t0 = time.perf_counter()
        try:
            resp = self.client.get("/health")
            duration = (time.perf_counter() - t0) * 1000
            if resp.status_code == 200 and resp.json().get("status") == "healthy":
                self.record_scenario("Health Endpoint Check", True, "API reported healthy status", duration)
            else:
                self.record_scenario("Health Endpoint Check", False, f"Unexpected health response: {resp.text}", duration)
        except Exception as e:
            self.record_scenario("Health Endpoint Check", False, str(e), (time.perf_counter() - t0) * 1000)

        # Storage directory check
        t0 = time.perf_counter()
        passed = CERTIFICATES_DIR.exists() and DATA_DIR.exists()
        self.record_scenario(
            "Storage & Data Dir Integrity",
            passed,
            f"Certificates Dir: {CERTIFICATES_DIR}",
            (time.perf_counter() - t0) * 1000
        )

    def test_bulk_generation_throughput(self, count: int = 20):
        self.log(f"\n[Scenario 2] Bulk Generation & Throughput Benchmark ({count} recipients)", Colors.BOLD)
        recipients = [
            {"name": f"Recipient #{i:02d} Tester", "email": f"tester{i}@qa-agent.org"}
            for i in range(1, count + 1)
        ]
        payload = {
            "title": "Autonomous QA Engineering Benchmark",
            "issuer_name": "Antigravity Testing Labs",
            "issue_date": "October 6, 2026",
            "description": "High-volume automated benchmark certification.",
            "recipients": recipients
        }

        t0 = time.perf_counter()
        resp = self.client.post("/api/v1/certificates/jobs", json=payload)
        t_submit = (time.perf_counter() - t0) * 1000

        if resp.status_code != 202:
            self.record_scenario("Batch Job Submission", False, f"Status {resp.status_code}: {resp.text}", t_submit)
            return

        job_id = resp.json()["job_id"]
        self.record_scenario("Batch Job Submission", True, f"Job accepted with UUID {job_id}", t_submit)

        # Monitor execution
        status_resp = self.client.get(f"/api/v1/certificates/jobs/{job_id}")
        data = status_resp.json()
        duration_total = (time.perf_counter() - t0) * 1000

        passed = data["status"] == "COMPLETED" and data["success_count"] == count
        certs_per_sec = (count / (duration_total / 1000.0)) if duration_total > 0 else 0
        self.report["performance_metrics"] = {
            "batch_size": count,
            "total_ms": round(duration_total, 2),
            "certificates_per_second": round(certs_per_sec, 2)
        }

        self.record_scenario(
            f"Bulk Batch Execution ({count} certs)",
            passed,
            f"Completed in {duration_total:.1f}ms (~{certs_per_sec:.1f} certs/sec). All {count} verified.",
            duration_total
        )
        self.active_batch_job_id = job_id

    def test_fault_tolerance_and_error_isolation(self):
        self.log("\n[Scenario 3] Fault Tolerance & Partial Failure Isolation", Colors.BOLD)
        payload = {
            "title": "Chaos & Fault Tolerance Certification",
            "issuer_name": "Aereo Reliability Board",
            "recipients": [
                {"name": "Valid Candidate A", "email": "candidate_a@test.org"},
                {"name": "Broken Email Candidate", "email": "corrupted-email-missing-domain"},
                {"name": "Valid Candidate B", "email": "candidate_b@test.org"}
            ]
        }
        t0 = time.perf_counter()
        resp = self.client.post("/api/v1/certificates/jobs", json=payload)
        job_id = resp.json()["job_id"]

        status_data = self.client.get(f"/api/v1/certificates/jobs/{job_id}").json()
        duration = (time.perf_counter() - t0) * 1000

        is_partial = status_data["status"] == "PARTIAL_SUCCESS"
        counts_match = status_data["success_count"] == 2 and status_data["failed_count"] == 1

        self.record_scenario(
            "Partial Failure Handling",
            is_partial and counts_match,
            f"Job correctly flagged PARTIAL_SUCCESS: 2 succeeded, 1 isolated failure.",
            duration
        )

        failed_certs = [c for c in status_data["certificates"] if c["status"] == "FAILED"]
        has_error_msg = len(failed_certs) == 1 and "Invalid email format" in (failed_certs[0]["error_message"] or "")
        self.record_scenario(
            "Error Message Granularity",
            has_error_msg,
            f"Recipient error accurately captured: '{failed_certs[0]['error_message']}'",
            1.0
        )

    def test_pdf_binary_integrity(self):
        self.log("\n[Scenario 4] PDF Binary & Format Integrity Audit", Colors.BOLD)
        t0 = time.perf_counter()
        # Fetch status of batch job
        job_data = self.client.get(f"/api/v1/certificates/jobs/{self.active_batch_job_id}").json()
        sample_cert = job_data["certificates"][0]
        cert_id = sample_cert["id"]

        dl_resp = self.client.get(f"/api/v1/certificates/{cert_id}/download")
        duration = (time.perf_counter() - t0) * 1000

        is_pdf_content = dl_resp.content.startswith(b"%PDF-")
        is_pdf_mime = dl_resp.headers.get("content-type") == "application/pdf"
        size_kb = len(dl_resp.content) / 1024

        self.record_scenario(
            "PDF Magic Header & MIME Verification",
            is_pdf_content and is_pdf_mime,
            f"Verified %PDF- header, MIME 'application/pdf', size: {size_kb:.1f} KB",
            duration
        )

    def test_zip_archive_integrity(self):
        self.log("\n[Scenario 5] ZIP Archive Bundle Packaging Verification", Colors.BOLD)
        t0 = time.perf_counter()
        zip_resp = self.client.get(f"/api/v1/certificates/jobs/{self.active_batch_job_id}/download-zip")
        duration = (time.perf_counter() - t0) * 1000

        try:
            zip_buf = io.BytesIO(zip_resp.content)
            with zipfile.ZipFile(zip_buf, "r") as zf:
                files = zf.namelist()
                all_pdfs = all(f.endswith(".pdf") for f in files)
                count_ok = len(files) == 20
                self.record_scenario(
                    "ZIP Bundle Integrity",
                    all_pdfs and count_ok,
                    f"Successfully unzipped {len(files)} certificates from batch archive.",
                    duration
                )
        except Exception as e:
            self.record_scenario("ZIP Bundle Integrity", False, f"ZIP extraction failed: {e}", duration)

    def test_verification_resolution(self):
        self.log("\n[Scenario 6] Certificate Authenticity Verification Endpoint", Colors.BOLD)
        job_data = self.client.get(f"/api/v1/certificates/jobs/{self.active_batch_job_id}").json()
        sample_cert = job_data["certificates"][0]
        code = sample_cert["certificate_code"]

        t0 = time.perf_counter()
        v_resp = self.client.get(f"/api/v1/certificates/verify/{code}")
        duration = (time.perf_counter() - t0) * 1000
        v_data = v_resp.json()

        valid_match = v_data.get("valid") is True and v_data.get("recipient_name") == sample_cert["recipient_name"]
        self.record_scenario(
            "Authentic Certificate Verification",
            valid_match,
            f"Resolved code {code} to {v_data.get('recipient_name')}",
            duration
        )

        # Fake code
        t0 = time.perf_counter()
        fake_resp = self.client.get("/api/v1/certificates/verify/FAKE-NON-EXISTENT-CODE")
        duration = (time.perf_counter() - t0) * 1000
        self.record_scenario(
            "Fraudulent / Invalid Code Rejection",
            fake_resp.json().get("valid") is False,
            "Properly rejected invalid verification query with valid=False",
            duration
        )

    def print_summary(self):
        self.log("\n" + "=" * 72, Colors.CYAN)
        self.log("  📊 QA AGENT EXECUTION SUMMARY", Colors.BOLD + Colors.CYAN)
        self.log("=" * 72, Colors.CYAN)
        self.log(f"  Total Checks Run : {self.report['tests_run']}")
        self.log(f"  Total Passed     : {self.report['tests_passed']}", Colors.GREEN)
        self.log(f"  Total Failed     : {self.report['tests_failed']}", Colors.RED if self.report['tests_failed'] > 0 else Colors.GREEN)
        self.log(f"  Total Time       : {self.report['total_execution_ms']} ms", Colors.BLUE)
        if "certificates_per_second" in self.report["performance_metrics"]:
            perf = self.report["performance_metrics"]
            self.log(f"  Throughput Speed : {perf['certificates_per_second']} certs/second", Colors.YELLOW)
        self.log("=" * 72, Colors.CYAN)

    def save_report(self):
        report_file = BASE_DIR / "qa_report.json"
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(self.report, f, indent=2)
        self.log(f"💾 QA Diagnostic Report saved to: {report_file}\n", Colors.CYAN)


if __name__ == "__main__":
    agent = QAAgent()
    agent.run_all()
    if agent.report["tests_failed"] > 0:
        sys.exit(1)
    sys.exit(0)
