"""
schema.py
Define el esquema Pydantic de output obligatorio según las specs del proyecto.
Campos requeridos: compliance_status, findings_count, executive_summary.
"""

from pydantic import BaseModel, field_validator, Field


class AuditResult(BaseModel):
    """
    Esquema validado de output para cada dossier auditado.
    El LLM debe producir exactamente estos campos con estas restricciones.
    """

    compliance_status: str = Field(
        description="Estado de cumplimiento. Debe ser exactamente 'Compliant' o 'Non-Compliant'."
    )

    findings_count: int = Field(
        description="Número entero de infracciones, registros faltantes o inconsistencias detectadas.",
        ge=0
    )

    executive_summary: str = Field(
        description="Resumen ejecutivo conciso del resultado de la auditoría. Máximo 500 caracteres."
    )

    @field_validator("compliance_status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        allowed = {"Compliant", "Non-Compliant"}
        if v not in allowed:
            raise ValueError(f"compliance_status debe ser 'Compliant' o 'Non-Compliant', recibido: '{v}'")
        return v

    @field_validator("executive_summary")
    @classmethod
    def validate_summary_length(cls, v: str) -> str:
        if len(v) > 500:
            raise ValueError(f"executive_summary excede 500 caracteres ({len(v)} recibidos). Debe ser más conciso.")
        return v

    @field_validator("findings_count")
    @classmethod
    def validate_findings_consistency(cls, v: int) -> int:
        if v < 0:
            raise ValueError("findings_count no puede ser negativo.")
        return v
