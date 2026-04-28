import uuid
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field

from src.domain.language import LanguageTagged


class ModuleId(StrEnum):
    """The five generation modules.

    Canonical execution order is encoded by the Orchestration Engine in
    src/orchestration/engine.py; this enum lists members only.
    """

    STRATEGY_THEME = "strategy_theme"
    TONE = "tone"
    NAMING = "naming"
    SLOGAN = "slogan"
    TAGLINE = "tagline"


class DecisionScope(BaseModel):
    """The non-empty subset of modules the client selected for this session.

    Per TDD §5.4 there are 31 valid Decision Scopes (2^5 - 1). Empty scope is
    rejected by `min_length=1`.
    """

    session_id: uuid.UUID
    modules: set[ModuleId] = Field(min_length=1)
    selected_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ExecutionPlan(BaseModel):
    """Ordered modules + applicable intersection pairs for a DecisionScope.

    The data SHAPE lives here; the function that PRODUCES the plan from a
    DecisionScope lives in src/orchestration/engine.py (Session 3).
    """

    session_id: uuid.UUID
    ordered_modules: list[ModuleId]
    intersection_pairs: list[tuple[ModuleId, ModuleId]] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ModuleOutput(LanguageTagged):
    """One module's generated result for one session.

    Per CLAUDE.md §2.7 every output carries its rationale (linked by id).
    Per §2.8 every LLM call that produced this output is logged in
    `llm_call_record_ids` (at least one).
    """

    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    session_id: uuid.UUID
    module: ModuleId
    register_id: uuid.UUID
    content: dict[str, Any]
    upstream_module_outputs: list[uuid.UUID] = Field(default_factory=list)
    rationale_id: uuid.UUID
    llm_call_record_ids: list[uuid.UUID] = Field(min_length=1)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
