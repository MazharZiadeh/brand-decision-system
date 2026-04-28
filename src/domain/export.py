import uuid
from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class ExportFormat(StrEnum):
    """Export formats supported by the Export Service. MVP ships PDF only."""

    PDF = "pdf"


class ExportArtifact(BaseModel):
    """Generated PDF metadata: location on disk + manifest of included content.

    The artifact bytes live on disk; this model is the audit/index record.
    """

    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    session_id: uuid.UUID
    format: ExportFormat
    file_path: str
    included_artifacts_manifest: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
