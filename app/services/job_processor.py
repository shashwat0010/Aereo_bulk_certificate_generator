import logging
import re
from datetime import datetime, timezone
from app.database import SessionLocal
from app.models import Job, Certificate, JobStatus, CertificateStatus
from app.services.certificate_generator import generate_certificate_pdf

logger = logging.getLogger("bulk_certificate_generator")
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def validate_recipient_record(name: str, email: str) -> str | None:
    """
    Validates recipient record during processing.
    Returns error message string if invalid, None if valid.
    """
    if not name or not name.strip():
        return "Recipient name is missing or blank."
    if not email or not email.strip():
        return "Recipient email is missing or blank."
    if not EMAIL_PATTERN.match(email.strip()):
        return f"Invalid email format: '{email}'"
    return None


def process_generation_job(job_id: str) -> None:
    """
    Background worker task to generate certificates for a given job.
    Processes each recipient independently, ensuring failures in individual
    recipients do not stop the remaining certificates from generating.
    """
    db = SessionLocal()
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            logger.error(f"Job {job_id} not found for processing.")
            return

        job.status = JobStatus.PROCESSING
        job.updated_at = datetime.now(timezone.utc)
        db.commit()

        certificates = db.query(Certificate).filter(Certificate.job_id == job_id).all()

        for cert in certificates:
            try:
                # 1. Validation check
                val_error = validate_recipient_record(cert.recipient_name, cert.recipient_email)
                if val_error:
                    cert.status = CertificateStatus.FAILED
                    cert.error_message = val_error
                    job.failed_count += 1
                else:
                    # 2. PDF Generation
                    pdf_path = generate_certificate_pdf(
                        certificate_id=cert.id,
                        certificate_code=cert.certificate_code,
                        recipient_name=cert.recipient_name,
                        title=job.title,
                        description=job.description,
                        issuer_name=job.issuer_name,
                        issue_date=job.issue_date,
                    )
                    cert.status = CertificateStatus.COMPLETED
                    cert.file_path = pdf_path
                    job.success_count += 1

            except Exception as ex:
                logger.exception(f"Error generating certificate {cert.id}: {ex}")
                cert.status = CertificateStatus.FAILED
                cert.error_message = f"Generation error: {str(ex)}"
                job.failed_count += 1

            job.processed_count += 1
            cert.updated_at = datetime.now(timezone.utc)
            db.commit()  # Commit progress per item for real-time tracking

        # Finalize job status
        if job.failed_count == 0:
            job.status = JobStatus.COMPLETED
        elif job.success_count > 0:
            job.status = JobStatus.PARTIAL_SUCCESS
        else:
            job.status = JobStatus.FAILED

        job.updated_at = datetime.now(timezone.utc)
        db.commit()
        logger.info(
            f"Completed Job {job_id} with status {job.status}. "
            f"Success: {job.success_count}, Failed: {job.failed_count}"
        )

    except Exception as ex:
        logger.exception(f"Fatal error processing job {job_id}: {ex}")
        if job:
            job.status = JobStatus.FAILED
            job.error_message = f"Job processing encountered fatal error: {str(ex)}"
            job.updated_at = datetime.now(timezone.utc)
            db.commit()
    finally:
        db.close()
