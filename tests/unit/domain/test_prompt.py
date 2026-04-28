import uuid

import pytest
from pydantic import ValidationError

from src.domain.module import ModuleId
from src.domain.prompt import ModulePromptExtension, SessionSystemPrompt


def _extension(module: ModuleId) -> ModulePromptExtension:
    return ModulePromptExtension(
        module=module,
        extension_text="Module-specific priorities…",
        schema_directive="Return {theme: str, justification: str}.",
    )


def test_module_prompt_extension_is_frozen():
    ext = _extension(ModuleId.STRATEGY_THEME)
    with pytest.raises(ValidationError):
        ext.extension_text = "different"  # type: ignore[misc]


def test_session_system_prompt_is_frozen():
    p = SessionSystemPrompt(
        session_id=uuid.uuid4(),
        unified_preamble="Brand DNA + Pain + Register…",
        module_extensions={ModuleId.STRATEGY_THEME: _extension(ModuleId.STRATEGY_THEME)},
        register_id=uuid.uuid4(),
        questionnaire_version_id=uuid.uuid4(),
        pain_analysis_id=uuid.uuid4(),
    )
    with pytest.raises(ValidationError):
        p.unified_preamble = "different"  # type: ignore[misc]


def test_session_system_prompt_required_fields():
    with pytest.raises(ValidationError):
        SessionSystemPrompt(  # type: ignore[call-arg]
            session_id=uuid.uuid4(),
            unified_preamble="…",
            module_extensions={},
        )
