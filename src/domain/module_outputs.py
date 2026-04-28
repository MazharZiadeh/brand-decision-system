"""Pydantic output schemas for the five generation modules.

Each module's LLM call is constrained to return JSON matching one of these
schemas. The Strategy Theme produces a `StrategyThemeOutput`, Tone produces
a `ToneOutput`, etc. The schemas are wired into the LLM provider's
structured-output mode in Session 5+; this file defines the contract.

Per CLAUDE.md §2.7, every module output carries
`priority_factors_addressed` — the rationale invariant is enforced at the
schema level via `min_length=2`. The factor type is the canonical
`PriorityFactor` from `src.domain.rationale`; one shape, one home.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from src.domain.language import LanguageTagged
from src.domain.rationale import PriorityFactor

# ── Strategy Theme ──────────────────────────────────────────────────────


class StrategyThemeOutput(LanguageTagged):
    """Strategy Theme module output: thematic positioning + elaboration + rationale."""

    theme: str = Field(..., description="One-sentence strategic theme.")
    elaboration: str = Field(..., description="2-3 sentences expanding the theme.")
    priority_factors_addressed: list[PriorityFactor] = Field(..., min_length=2)


# ── Tone ────────────────────────────────────────────────────────────────


class ToneOutput(LanguageTagged):
    """Tone module output: descriptor + do/don't lists + optional Arabic note."""

    descriptor: str = Field(
        ...,
        description="A few adjectives or a short phrase capturing the tone.",
    )
    do_examples: list[str] = Field(..., min_length=3, max_length=5)
    dont_examples: list[str] = Field(..., min_length=3, max_length=5)
    arabic_note: str | None = Field(
        default=None,
        description="Arabic-specific tone guidance, when applicable.",
    )
    priority_factors_addressed: list[PriorityFactor] = Field(..., min_length=2)


# ── Naming ──────────────────────────────────────────────────────────────


class NameCandidate(BaseModel):
    """One name candidate with rationale and optional Arabic form."""

    model_config = ConfigDict(frozen=True)

    name: str
    rationale: str
    arabic_form: str | None = Field(
        default=None,
        description="Arabic transliteration or equivalent if name is non-Arabic.",
    )


class NamingOutput(LanguageTagged):
    """Naming module output: 3-5 candidates with rationale per candidate."""

    candidates: list[NameCandidate] = Field(..., min_length=3, max_length=5)
    priority_factors_addressed: list[PriorityFactor] = Field(..., min_length=2)


# ── Slogan ──────────────────────────────────────────────────────────────


class SloganOption(BaseModel):
    """One slogan option with rationale (internal-rallying, not customer-facing)."""

    model_config = ConfigDict(frozen=True)

    slogan: str
    rationale: str


class SloganOutput(LanguageTagged):
    """Slogan module output: 2-3 internal-rallying options."""

    options: list[SloganOption] = Field(..., min_length=2, max_length=3)
    priority_factors_addressed: list[PriorityFactor] = Field(..., min_length=2)


# ── Tagline ─────────────────────────────────────────────────────────────


class TaglineOption(BaseModel):
    """One tagline option with rationale and the dominant feeling it aims to evoke."""

    model_config = ConfigDict(frozen=True)

    tagline: str
    rationale: str
    intended_feeling: str = Field(
        ...,
        description="The dominant feeling this tagline aims to evoke.",
    )


class TaglineOutput(LanguageTagged):
    """Tagline module output: 2-3 customer-facing options."""

    options: list[TaglineOption] = Field(..., min_length=2, max_length=3)
    priority_factors_addressed: list[PriorityFactor] = Field(..., min_length=2)


__all__ = [
    "NameCandidate",
    "NamingOutput",
    "SloganOption",
    "SloganOutput",
    "StrategyThemeOutput",
    "TaglineOption",
    "TaglineOutput",
    "ToneOutput",
]
