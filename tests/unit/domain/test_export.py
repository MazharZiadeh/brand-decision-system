import uuid

import pytest
from pydantic import ValidationError

from src.domain.export import ExportArtifact, ExportFormat


def test_export_format_pdf_only_in_mvp():
    assert {f.value for f in ExportFormat} == {"pdf"}


def test_valid_export_artifact():
    a = ExportArtifact(
        session_id=uuid.uuid4(),
        format=ExportFormat.PDF,
        file_path="/exports/session-abc.pdf",
        included_artifacts_manifest=["questionnaire", "pain_analysis", "module_outputs"],
    )
    assert a.format == ExportFormat.PDF
    assert "questionnaire" in a.included_artifacts_manifest


def test_format_required():
    with pytest.raises(ValidationError):
        ExportArtifact(  # type: ignore[call-arg]
            session_id=uuid.uuid4(),
            file_path="/exports/x.pdf",
        )
