from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator
from datetime import date
import re

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class RecipientInput(BaseModel):
    name: str = Field(..., description="Recipient full name", min_length=1)
    email: str = Field(..., description="Recipient email address", min_length=3)
    custom_attributes: Optional[Dict[str, Any]] = Field(
        default=None, description="Optional custom metadata e.g. score, grade"
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        clean = v.strip()
        if not clean:
            raise ValueError("Recipient name cannot be empty or whitespace.")
        return clean

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        clean = v.strip().lower()
        if not clean:
            raise ValueError("Recipient email cannot be empty.")
        return clean


class JobCreateRequest(BaseModel):
    title: str = Field(..., description="Certificate title or course name", min_length=1)
    description: Optional[str] = Field(
        default="For successful completion and demonstrated excellence in the program.",
        description="Reason or achievement description"
    )
    issuer_name: str = Field(..., description="Issuing organization or authority", min_length=1)
    issue_date: Optional[str] = Field(
        default_factory=lambda: date.today().strftime("%B %d, %Y"),
        description="Issue date (e.g., 'October 6, 2026'). Defaults to current date if omitted."
    )
    recipients: List[RecipientInput] = Field(
        ...,
        description="List of recipients to generate certificates for",
        min_length=1
    )

    @field_validator("title", "issuer_name")
    @classmethod
    def validate_non_empty(cls, v: str) -> str:
        clean = v.strip()
        if not clean:
            raise ValueError("Field cannot be empty or whitespace.")
        return clean

    @field_validator("issue_date")
    @classmethod
    def set_default_date(cls, v: Optional[str]) -> str:
        if not v or not v.strip():
            return date.today().strftime("%B %d, %Y")
        return v.strip()


class CertificateSummaryResponse(BaseModel):
    id: str
    recipient_name: str
    recipient_email: str
    certificate_code: str
    status: str
    error_message: Optional[str] = None
    download_url: Optional[str] = None


class JobResponse(BaseModel):
    job_id: str
    title: str
    description: Optional[str] = None
    issuer_name: str
    issue_date: str
    status: str
    total_count: int
    processed_count: int
    success_count: int
    failed_count: int
    error_message: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class JobDetailResponse(JobResponse):
    certificates: List[CertificateSummaryResponse] = []
    zip_download_url: Optional[str] = None


class CertificateVerificationResponse(BaseModel):
    valid: bool
    certificate_code: str
    recipient_name: Optional[str] = None
    recipient_email: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    issuer_name: Optional[str] = None
    issue_date: Optional[str] = None
    issued_at: Optional[str] = None
    message: Optional[str] = None
