import uuid
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from src.domain.language import Language, LanguageTagged


class PainCategory(BaseModel):
    """One category in the expert-authored pain taxonomy."""

    model_config = ConfigDict(frozen=True)

    id: str
    name_by_language: dict[Language, str]
    description_by_language: dict[Language, str]
    example_by_language: dict[Language, str] | None = None


class PainTaxonomy(BaseModel):
    """The fixed, expert-authored set of pain categories. Versioned and immutable."""

    model_config = ConfigDict(frozen=True)

    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    version: str
    categories: list[PainCategory]
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class RuleTrigger(BaseModel):
    """Declarative description of an answer pattern that fires a Rule.

    The Rules Engine (Session 6+) consumes these triggers; this model only
    holds the declarative shape, no evaluation logic.
    """

    model_config = ConfigDict(frozen=True)

    question_id: str
    operator: str
    value: Any


class Rule(BaseModel):
    """A declarative mapping from an answer pattern to one PainCategory."""

    model_config = ConfigDict(frozen=True)

    id: str
    pain_category_id: str
    trigger: RuleTrigger


class PainAnalysis(LanguageTagged):
    """Combined Rules-Engine tags and LLM-elaborated narrative for one session.

    Per CLAUDE.md §2.8 every LLM-backed output traces to at least one
    LLMCallRecord; the list shape supports future self-critique loops or
    N-best narrative sampling without a schema migration. `register_id`
    pins the narrative to the specific LanguageRegister directive that
    shaped it, so the audit chain narrative → register stays explicit.
    """

    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    session_id: uuid.UUID
    tagged_pain_categories: list[str]
    register_id: uuid.UUID
    narrative: str
    rationale_id: uuid.UUID
    llm_call_record_ids: list[uuid.UUID] = Field(min_length=1)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
