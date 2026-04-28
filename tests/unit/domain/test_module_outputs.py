"""Validation tests for the per-module output schemas.

Each schema is exercised four ways: a valid construction, a missing-field
rejection, a Field-constraint rejection (length bounds), and the
LanguageTagged invariant (language is required).
"""

import pytest
from pydantic import ValidationError

from src.domain.language import Language
from src.domain.module_outputs import (
    NameCandidate,
    NamingOutput,
    SloganOption,
    SloganOutput,
    StrategyThemeOutput,
    TaglineOption,
    TaglineOutput,
    ToneOutput,
)
from src.domain.rationale import PriorityFactor


def _factors() -> list[PriorityFactor]:
    return [
        PriorityFactor(
            factor_name="Position fit",
            how_addressed="Anchored on premium without performative luxury.",
        ),
        PriorityFactor(
            factor_name="Pain alignment: obscurity",
            how_addressed="Theme implies recognition through specificity.",
        ),
    ]


# ── PriorityFactor ─────────────────────────────────────────


def test_priority_factor_addressed_is_frozen():
    pf = PriorityFactor(factor_name="X", how_addressed="Y")
    with pytest.raises(ValidationError):
        pf.factor_name = "Z"  # type: ignore[misc]


# ── StrategyThemeOutput ─────────────────────────────────────────────


def test_strategy_theme_output_valid():
    out = StrategyThemeOutput(
        language=Language.ENGLISH,
        theme="Quietly engineered for the Saudi professional who wants quality without theatre.",
        elaboration="The brand commits to substance over signal. Every product detail is the answer.",
        priority_factors_addressed=_factors(),
    )
    assert out.theme.startswith("Quietly")
    assert out.language == Language.ENGLISH


def test_strategy_theme_output_requires_language():
    with pytest.raises(ValidationError):
        StrategyThemeOutput(  # type: ignore[call-arg]
            theme="…",
            elaboration="…",
            priority_factors_addressed=_factors(),
        )


def test_strategy_theme_output_requires_theme():
    with pytest.raises(ValidationError):
        StrategyThemeOutput(  # type: ignore[call-arg]
            language=Language.ENGLISH,
            elaboration="…",
            priority_factors_addressed=_factors(),
        )


def test_strategy_theme_output_requires_at_least_two_priority_factors():
    with pytest.raises(ValidationError):
        StrategyThemeOutput(
            language=Language.ENGLISH,
            theme="…",
            elaboration="…",
            priority_factors_addressed=[_factors()[0]],
        )


# ── ToneOutput ──────────────────────────────────────────────────────


def test_tone_output_valid():
    out = ToneOutput(
        language=Language.ENGLISH,
        descriptor="Confident, warm, deliberate — the trusted craftsman.",
        do_examples=[
            "Say what we mean, in fewer words.",
            "Lead with the customer's situation.",
            "Stand by the work without bluster.",
        ],
        dont_examples=[
            "Don't say 'innovative solutions'.",
            "Don't use exclamation marks.",
            "Don't start sentences with 'we are passionate about'.",
        ],
        priority_factors_addressed=_factors(),
    )
    assert out.arabic_note is None


def test_tone_output_requires_three_do_examples():
    with pytest.raises(ValidationError):
        ToneOutput(
            language=Language.ENGLISH,
            descriptor="…",
            do_examples=["one", "two"],
            dont_examples=["a", "b", "c"],
            priority_factors_addressed=_factors(),
        )


def test_tone_output_caps_do_examples_at_five():
    with pytest.raises(ValidationError):
        ToneOutput(
            language=Language.ENGLISH,
            descriptor="…",
            do_examples=["1", "2", "3", "4", "5", "6"],
            dont_examples=["a", "b", "c"],
            priority_factors_addressed=_factors(),
        )


def test_tone_output_arabic_note_optional():
    out = ToneOutput(
        language=Language.ARABIC,
        descriptor="واثق، دافئ، متأنٍّ.",
        do_examples=["…", "…", "…"],
        dont_examples=["…", "…", "…"],
        arabic_note="فضّل الجمل القصيرة في العربية.",
        priority_factors_addressed=_factors(),
    )
    assert out.arabic_note is not None


# ── NamingOutput ────────────────────────────────────────────────────


def test_naming_output_valid():
    out = NamingOutput(
        language=Language.ENGLISH,
        candidates=[
            NameCandidate(name="Sirr", rationale="Arabic root for 'essence'.", arabic_form="سِرّ"),
            NameCandidate(name="North Reed", rationale="Direction + craft.", arabic_form=None),
            NameCandidate(name="Beyat", rationale="Root for 'home'.", arabic_form="بيات"),
        ],
        priority_factors_addressed=_factors(),
    )
    assert len(out.candidates) == 3


def test_naming_output_rejects_two_candidates():
    with pytest.raises(ValidationError):
        NamingOutput(
            language=Language.ENGLISH,
            candidates=[
                NameCandidate(name="A", rationale="…"),
                NameCandidate(name="B", rationale="…"),
            ],
            priority_factors_addressed=_factors(),
        )


def test_naming_output_rejects_six_candidates():
    with pytest.raises(ValidationError):
        NamingOutput(
            language=Language.ENGLISH,
            candidates=[NameCandidate(name=str(i), rationale="…") for i in range(6)],
            priority_factors_addressed=_factors(),
        )


def test_name_candidate_is_frozen():
    c = NameCandidate(name="X", rationale="Y")
    with pytest.raises(ValidationError):
        c.name = "Z"  # type: ignore[misc]


def test_naming_output_requires_language():
    with pytest.raises(ValidationError):
        NamingOutput(  # type: ignore[call-arg]
            candidates=[
                NameCandidate(name="A", rationale="…"),
                NameCandidate(name="B", rationale="…"),
                NameCandidate(name="C", rationale="…"),
            ],
            priority_factors_addressed=_factors(),
        )


# ── SloganOutput ────────────────────────────────────────────────────


def test_slogan_output_valid():
    out = SloganOutput(
        language=Language.ENGLISH,
        options=[
            SloganOption(slogan="Build > Talk", rationale="Reinforces builder identity."),
            SloganOption(slogan="Ship the truth", rationale="Pain alignment: action_misalignment."),
        ],
        priority_factors_addressed=_factors(),
    )
    assert len(out.options) == 2


def test_slogan_output_caps_at_three_options():
    with pytest.raises(ValidationError):
        SloganOutput(
            language=Language.ENGLISH,
            options=[SloganOption(slogan=str(i), rationale="…") for i in range(4)],
            priority_factors_addressed=_factors(),
        )


def test_slogan_output_requires_at_least_two_options():
    with pytest.raises(ValidationError):
        SloganOutput(
            language=Language.ENGLISH,
            options=[SloganOption(slogan="X", rationale="…")],
            priority_factors_addressed=_factors(),
        )


def test_slogan_output_requires_language():
    with pytest.raises(ValidationError):
        SloganOutput(  # type: ignore[call-arg]
            options=[
                SloganOption(slogan="A", rationale="…"),
                SloganOption(slogan="B", rationale="…"),
            ],
            priority_factors_addressed=_factors(),
        )


# ── TaglineOutput ───────────────────────────────────────────────────


def test_tagline_output_valid():
    out = TaglineOutput(
        language=Language.ENGLISH,
        options=[
            TaglineOption(
                tagline="Built to last, made to belong.",
                rationale="Emotion: belonging.",
                intended_feeling="belonging",
            ),
            TaglineOption(
                tagline="Quiet strength, made here.",
                rationale="Emotion: trust + cultural anchor.",
                intended_feeling="trust",
            ),
        ],
        priority_factors_addressed=_factors(),
    )
    assert out.options[0].intended_feeling == "belonging"


def test_tagline_option_requires_intended_feeling():
    with pytest.raises(ValidationError):
        TaglineOption(  # type: ignore[call-arg]
            tagline="X",
            rationale="Y",
        )


def test_tagline_output_caps_at_three_options():
    with pytest.raises(ValidationError):
        TaglineOutput(
            language=Language.ENGLISH,
            options=[
                TaglineOption(tagline=str(i), rationale="…", intended_feeling="trust")
                for i in range(4)
            ],
            priority_factors_addressed=_factors(),
        )


def test_tagline_output_requires_language():
    with pytest.raises(ValidationError):
        TaglineOutput(  # type: ignore[call-arg]
            options=[
                TaglineOption(tagline="A", rationale="…", intended_feeling="trust"),
                TaglineOption(tagline="B", rationale="…", intended_feeling="trust"),
            ],
            priority_factors_addressed=_factors(),
        )
