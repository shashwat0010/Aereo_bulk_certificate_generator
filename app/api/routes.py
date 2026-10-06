import io
import json
import uuid
import zipfile
from datetime import date
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status, Query
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Job, Certificate, JobStatus, CertificateStatus
from app.schemas import (
    JobCreateRequest,
    JobResponse,
    JobDetailResponse,
    CertificateSummaryResponse,
    CertificateVerificationResponse,
)
from app.services.job_processor import process_generation_job
from app.config import CERTIFICATES_DIR

router = APIRouter(prefix="/api/v1", tags=["Certificates"])


def make_cert_code() -> str:
    """Generate a clean, readable unique certificate verification code."""
    return f"CERT-{uuid.uuid4().hex[:10].upper()}"


@router.post(
    "/certificates/jobs",
    response_model=JobResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Create Bulk Certificate Generation Job",
    description="Submits a bulk certificate request. Validates payload and starts asynchronous background generation."
)
def create_generation_job(
    request: JobCreateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    if not request.recipients:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Recipients list cannot be empty."
        )

    # 1. Create Job record
    issue_date = request.issue_date or date.today().strftime("%B %d, %Y")
    new_job = Job(
        title=request.title,
        description=request.description,
        issuer_name=request.issuer_name,
        issue_date=issue_date,
        status=JobStatus.PENDING,
        total_count=len(request.recipients),
        processed_count=0,
        success_count=0,
        failed_count=0,
    )
    db.add(new_job)
    db.flush()  # assign job ID

    # 2. Create Certificate records
    cert_records = []
    for r in request.recipients:
        custom_attr_str = json.dumps(r.custom_attributes) if r.custom_attributes else None
        cert = Certificate(
            job_id=new_job.id,
            recipient_name=r.name,
            recipient_email=r.email,
            certificate_code=make_cert_code(),
            status=CertificateStatus.PENDING,
            custom_attributes=custom_attr_str,
        )
        cert_records.append(cert)

    db.add_all(cert_records)
    db.commit()
    db.refresh(new_job)

    # 3. Dispatch to background processor
    background_tasks.add_task(process_generation_job, new_job.id)

    return JobResponse(
        job_id=new_job.id,
        title=new_job.title,
        description=new_job.description,
        issuer_name=new_job.issuer_name,
        issue_date=new_job.issue_date,
        status=new_job.status,
        total_count=new_job.total_count,
        processed_count=new_job.processed_count,
        success_count=new_job.success_count,
        failed_count=new_job.failed_count,
        created_at=new_job.created_at.isoformat() if new_job.created_at else None,
        updated_at=new_job.updated_at.isoformat() if new_job.updated_at else None,
    )


@router.get(
    "/certificates/jobs/{job_id}",
    response_model=JobDetailResponse,
    summary="Get Job Status and Details",
    description="Check the current progress, counts, and per-recipient certificate status for a job."
)
def get_job_status(job_id: str, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Job '{job_id}' not found.")

    certs = db.query(Certificate).filter(Certificate.job_id == job_id).all()

    cert_summaries = []
    for c in certs:
        download_url = f"/api/v1/certificates/{c.id}/download" if c.status == CertificateStatus.COMPLETED else None
        cert_summaries.append(
            CertificateSummaryResponse(
                id=c.id,
                recipient_name=c.recipient_name,
                recipient_email=c.recipient_email,
                certificate_code=c.certificate_code,
                status=c.status,
                error_message=c.error_message,
                download_url=download_url,
            )
        )

    zip_url = f"/api/v1/certificates/jobs/{job.id}/download-zip" if job.success_count > 0 else None

    return JobDetailResponse(
        job_id=job.id,
        title=job.title,
        description=job.description,
        issuer_name=job.issuer_name,
        issue_date=job.issue_date,
        status=job.status,
        total_count=job.total_count,
        processed_count=job.processed_count,
        success_count=job.success_count,
        failed_count=job.failed_count,
        error_message=job.error_message,
        created_at=job.created_at.isoformat() if job.created_at else None,
        updated_at=job.updated_at.isoformat() if job.updated_at else None,
        certificates=cert_summaries,
        zip_download_url=zip_url,
    )


@router.get(
    "/certificates/jobs",
    response_model=List[JobResponse],
    summary="List Certificate Generation Jobs",
    description="Returns a list of all certificate generation jobs."
)
def list_jobs(limit: int = 50, offset: int = 0, db: Session = Depends(get_db)):
    jobs = db.query(Job).order_by(Job.created_at.desc()).offset(offset).limit(limit).all()
    return [
        JobResponse(
            job_id=j.id,
            title=j.title,
            description=j.description,
            issuer_name=j.issuer_name,
            issue_date=j.issue_date,
            status=j.status,
            total_count=j.total_count,
            processed_count=j.processed_count,
            success_count=j.success_count,
            failed_count=j.failed_count,
            error_message=j.error_message,
            created_at=j.created_at.isoformat() if j.created_at else None,
            updated_at=j.updated_at.isoformat() if j.updated_at else None,
        )
        for j in jobs
    ]


@router.get(
    "/certificates/jobs/{job_id}/certificates",
    response_model=List[CertificateSummaryResponse],
    summary="List Certificates in a Job",
    description="Returns certificates belonging to a job, optionally filtered by status."
)
def list_job_certificates(
    job_id: str,
    status_filter: Optional[str] = Query(None, alias="status"),
    db: Session = Depends(get_db)
):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Job '{job_id}' not found.")

    query = db.query(Certificate).filter(Certificate.job_id == job_id)
    if status_filter:
        query = query.filter(Certificate.status == status_filter.upper())
    certs = query.all()

    return [
        CertificateSummaryResponse(
            id=c.id,
            recipient_name=c.recipient_name,
            recipient_email=c.recipient_email,
            certificate_code=c.certificate_code,
            status=c.status,
            error_message=c.error_message,
            download_url=f"/api/v1/certificates/{c.id}/download" if c.status == CertificateStatus.COMPLETED else None,
        )
        for c in certs
    ]


@router.get(
    "/certificates/{certificate_id}/download",
    summary="Download Individual Certificate PDF",
    description="Downloads the generated PDF certificate as an attachment."
)
def download_certificate(certificate_id: str, db: Session = Depends(get_db)):
    cert = db.query(Certificate).filter(Certificate.id == certificate_id).first()
    if not cert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Certificate '{certificate_id}' not found.")

    if cert.status != CertificateStatus.COMPLETED or not cert.file_path:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Certificate is not ready. Current status: {cert.status}. Error: {cert.error_message or 'None'}"
        )

    file_path = Path(cert.file_path)
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Generated certificate file not found on disk."
        )

    clean_name = "".join(ch if ch.isalnum() or ch in ("-", "_") else "_" for ch in cert.recipient_name)
    filename = f"{clean_name}_Certificate.pdf"

    return FileResponse(
        path=str(file_path),
        media_type="application/pdf",
        filename=filename,
    )


@router.get(
    "/certificates/{certificate_id}/preview",
    summary="Preview Certificate PDF Inline",
    description="Renders the PDF directly in the browser viewer."
)
def preview_certificate(certificate_id: str, db: Session = Depends(get_db)):
    cert = db.query(Certificate).filter(Certificate.id == certificate_id).first()
    if not cert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Certificate not found.")

    if cert.status != CertificateStatus.COMPLETED or not cert.file_path:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Certificate not generated yet.")

    file_path = Path(cert.file_path)
    if not file_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Certificate file not found.")

    return FileResponse(
        path=str(file_path),
        media_type="application/pdf",
        headers={"Content-Disposition": "inline"},
    )


@router.get(
    "/certificates/jobs/{job_id}/download-zip",
    summary="Download All Certificates in a ZIP Archive",
    description="Packages all successfully generated certificates for a job into a downloadable ZIP archive."
)
def download_job_certificates_zip(job_id: str, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Job '{job_id}' not found.")

    certs = db.query(Certificate).filter(
        Certificate.job_id == job_id,
        Certificate.status == CertificateStatus.COMPLETED
    ).all()

    if not certs:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No completed certificates available for download in this job."
        )

    # Build ZIP archive in memory
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        used_names = set()
        for cert in certs:
            if cert.file_path and Path(cert.file_path).exists():
                clean_name = "".join(ch if ch.isalnum() or ch in ("-", "_") else "_" for ch in cert.recipient_name)
                base_name = f"{clean_name}_{cert.certificate_code}"
                final_name = f"{base_name}.pdf"
                zf.write(cert.file_path, arcname=final_name)

    zip_buffer.seek(0)
    zip_filename = f"Certificates_Job_{job_id[:8]}.zip"

    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{zip_filename}"'}
    )


@router.get(
    "/certificates/verify/{certificate_code}",
    response_model=CertificateVerificationResponse,
    summary="Verify Certificate Authenticity",
    description="Validates a certificate code against issued certificates."
)
def verify_certificate(certificate_code: str, db: Session = Depends(get_db)):
    cert = db.query(Certificate).filter(Certificate.certificate_code == certificate_code).first()
    if not cert:
        return CertificateVerificationResponse(
            valid=False,
            certificate_code=certificate_code,
            message="Certificate code not found in our records."
        )

    if cert.status != CertificateStatus.COMPLETED:
        return CertificateVerificationResponse(
            valid=False,
            certificate_code=certificate_code,
            message=f"Certificate exists but is not valid. Status: {cert.status}"
        )

    job = cert.job
    return CertificateVerificationResponse(
        valid=True,
        certificate_code=cert.certificate_code,
        recipient_name=cert.recipient_name,
        recipient_email=cert.recipient_email,
        title=job.title if job else "N/A",
        description=job.description if job else "N/A",
        issuer_name=job.issuer_name if job else "N/A",
        issue_date=job.issue_date if job else "N/A",
        issued_at=cert.created_at.strftime("%B %d, %Y") if cert.created_at else None,
        message="Certificate is authentic and officially issued."
    )
