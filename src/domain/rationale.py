import uuid
from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, Field

from src.domain.language import LanguageTagged


class PriorityFactor(BaseModel):
    """One priority factor a generated output addressed.

    Factor names are NOT enum'd because they are module-specific (e.g.,
    "Audience perception" for Tone, "Strategic positioning" for Strategy).
    The accompanying `how_addressed` text is the per-output narrative
    explaining how the factor was served.
    """

    model_config = ConfigDict(frozen=True)

    factor_name: str
    how_addressed: str


class Rationale(LanguageTagged):
    """Structured justification attached to every LLM-backed output.

    Per CLAUDE.md §2.7, every Pain Narrative and every Module Output is a
    triple (output, rationale, priority factors addressed). This model holds
    the rationale and priority factors; the linkage is by id from the parent
    output.
    """

    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    priority_factors_addressed: list[PriorityFactor]
    narrative: str
    upstream_inputs_referenced: list[uuid.UUID] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
