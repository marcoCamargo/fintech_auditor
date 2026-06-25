"""
schema.py — Pydantic output schema for the FinTech Compliance Auditor.

Defines the exact structure the LLM must return for every dossier.
The PydanticOutputParser in chain.py uses this class to validate and
deserialize the model's JSON response — any violation raises a
ValidationError and the dossier is recorded as a failed audit.
"""

import logging
from pydantic import BaseModel, field_validator, Field

logger = logging.getLogger("fintech_auditor")


class AuditResult(BaseModel):
    """
    Validated output record for a single audited dossier.

    All three fields are required. The LLM is instructed to produce
    exactly this structure via PydanticOutputParser.get_format_instructions().
    """

    compliance_status: str = Field(
        description="Overall compliance verdict. Must be exactly 'Compliant' or 'Non-Compliant'."
    )

    findings_count: int = Field(
        description="Number of distinct violations, missing records, or inconsistencies detected. Must be >= 0.",
        ge=0
    )

    executive_summary: str = Field(
        description="Concise audit summary for the dossier. Maximum 500 characters."
    )

    @field_validator("compliance_status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        allowed = {"Compliant", "Non-Compliant"}
        if v not in allowed:
            raise ValueError(f"compliance_status must be 'Compliant' or 'Non-Compliant', got: '{v}'")
        return v

    @field_validator("executive_summary")
    @classmethod
    def validate_summary_length(cls, v: str) -> str:
        if len(v) > 500:
            # Truncate instead of rejecting the whole audit result over a minor overage.
            # Cut at the last word boundary before char 500 to avoid splitting mid-word.
            truncated = v[:500].rsplit(" ", 1)[0]
            logger.warning(
                f"  [SCHEMA] executive_summary truncated from {len(v)} to {len(truncated)} characters"
            )
            return truncated
        return v

    @field_validator("findings_count")
    @classmethod
    def validate_findings_consistency(cls, v: int) -> int:
        if v < 0:
            raise ValueError("findings_count cannot be negative.")
        return v
