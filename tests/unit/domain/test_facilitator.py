from datetime import datetime

import pytest
from pydantic import ValidationError

from src.domain.facilitator import Facilitator


def test_valid_facilitator():
    f = Facilitator(email="ops@example.com", display_name="Ops User")
    assert f.email == "ops@example.com"
    assert f.display_name == "Ops User"
    assert isinstance(f.created_at, datetime)


def test_email_required():
    with pytest.raises(ValidationError):
        Facilitator(display_name="No Email")  # type: ignore[call-arg]


def test_invalid_email_rejected():
    with pytest.raises(ValidationError):
        Facilitator(email="not-an-email", display_name="Bad")
