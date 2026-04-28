import uuid
from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, Field

from src.domain.module import ModuleId


class ModulePromptExtension(BaseModel):
    """Per-module addition to the unified preamble.

    The extension carries the module-specific priority hierarchy and output
    schema directive. The Jinja2 templates that produce the extension text
    live in `content/prompts/modules/`; the builder that fills them lives in
    `src/generation/prompt_builder.py` (Session 7+).
    """

    model_config = ConfigDict(frozen=True)

    module: ModuleId
    extension_text: str
    schema_directive: str


class SessionSystemPrompt(BaseModel):
    """The assembled, ready-to-use Session System Prompt.

    The unified preamble carries Brand DNA Profile, Pain Analysis, and Language
    Register — context every active module receives identically. The per-module
    extensions carry the module-specific priority hierarchy and output schema
    directive.

    This model represents the BUILT prompt object. The templates and the
    building logic are not in this session.
    """

    model_config = ConfigDict(frozen=True)

    session_id: uuid.UUID
    unified_preamble: str
    module_extensions: dict[ModuleId, ModulePromptExtension]
    register_id: uuid.UUID
    questionnaire_version_id: uuid.UUID
    pain_analysis_id: uuid.UUID
    built_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
