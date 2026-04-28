"""Pinned LLM model version identifiers.

Per CLAUDE.md §2.9, model versions are determinism boundaries. Pinning them
as constants in code (not config) means a code review is required to change
them — silent migration to a new model version is impossible.

Real provider model identifiers are added when the bake-off completes and
the corresponding adapter is built. Until then, only the mock identifiers
are present.
"""

from enum import StrEnum


class ModelVersion(StrEnum):
    """Pinned model version identifiers."""

    MOCK_FIXED = "mock-fixed-v1"
    MOCK_VARIABLE = "mock-variable-v1"

    # Real providers will land here, e.g.:
    # CLAUDE_OPUS_4_7 = "claude-opus-4-7"
    # GEMINI_2_5_PRO = "gemini-2.5-pro-002"
    # GPT_5_TURBO = "gpt-5-turbo-2026-01"
