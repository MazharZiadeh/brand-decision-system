import uuid
from datetime import datetime

import pytest
from pydantic import ValidationError

from src.domain.session import PhaseState, Session


def test_valid_session_defaults_to_discovery():
    s = Session(
        facilitator_id=uuid.uuid4(),
        questionnaire_version_id=uuid.uuid4(),
    )
    assert s.phase == PhaseState.DISCOVERY
    assert isinstance(s.created_at, datetime)
    assert isinstance(s.updated_at, datetime)


def test_facilitator_id_required():
    with pytest.raises(ValidationError):
        Session(questionnaire_version_id=uuid.uuid4())  # type: ignore[call-arg]


def test_questionnaire_version_id_required():
    with pytest.raises(ValidationError):
        Session(facilitator_id=uuid.uuid4())  # type: ignore[call-arg]


def test_phase_state_enum_values():
    assert {p.value for p in PhaseState} == {
        "discovery",
        "decision",
        "generation",
        "delivered",
    }


def test_phase_can_advance():
    s = Session(
        facilitator_id=uuid.uuid4(),
        questionnaire_version_id=uuid.uuid4(),
        phase=PhaseState.GENERATION,
    )
    assert s.phase == PhaseState.GENERATION
