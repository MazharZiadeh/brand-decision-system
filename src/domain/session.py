import uuid
from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class PhaseState(StrEnum):
    """The four phase states of a session.

    Per CLAUDE.md §2.10, phases run in fixed order:
    DISCOVERY → DECISION → GENERATION → DELIVERED.
    """

    DISCOVERY = "discovery"
    DECISION = "decision"
    GENERATION = "generation"
    DELIVERED = "delivered"


class Session(BaseModel):
    """Top-level container for one meeting.

    Per TDD §7, a Session belongs to one Facilitator and references exactly
    one QuestionnaireVersion, fixed at creation.
    """

    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    facilitator_id: uuid.UUID
    questionnaire_version_id: uuid.UUID
    phase: PhaseState = PhaseState.DISCOVERY
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
