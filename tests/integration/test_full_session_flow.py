"""Full session flow: Discovery → Decision → Generation, end-to-end with the Mock LLM.

Loads the real content tree, runs the rules engine and register
resolver against a fixture Discovery answer set, generates the pain
narrative, builds an ExecutionPlan for all 5 modules, runs the
generation orchestrator, and asserts the audit chain stays intact
across every module + the narrative.

Marked `integration` because it touches the filesystem (content load,
template render) and exercises the full pipeline. It does NOT touch
the database — persistence is Session 8's concern.
"""

from __future__ import annotations

import uuid

import pytest

from src.discovery import (
    load_content_bundle,
    resolve_register,
    tag_pain_categories,
)
from src.domain.brand_dna_context import build_brand_dna_context
from src.domain.language import Language
from src.domain.module import DecisionScope, ModuleId
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
from src.domain.narrative_output import PainNarrativeOutput
from src.domain.questionnaire import Answer
from src.domain.rationale import PriorityFactor
from src.generation import generate_pain_narrative
from src.generation.orchestrator import run_generation
from src.llm.mock import MockLLMProvider
from src.orchestration.engine import build_execution_plan

pytestmark = pytest.mark.integration


def _ans(question_id: str, value):
    return Answer(question_id=question_id, value=value, language=Language.ENGLISH)


def _full_session_fixture_answers() -> list[Answer]:
    """22 valid Answer objects matching the v0.1 questionnaire's 22 questions
    for an "invisible premium brand" — Q3.1 + Q3.2 are low so the rules
    engine tags obscurity + commoditization."""
    return [
        _ans("q1.1", "TestBrand. We make premium professional bags for Saudi business travelers."),
        _ans("q1.2", "early"),
        _ans("q1.3", "premium"),
        _ans("q1.4", 50),
        _ans("q2.1", "Saudi business professionals 30-45 who travel weekly."),
        _ans("q2.2", 50),
        _ans("q2.3", 70),
        _ans("q2.4", 60),
        _ans("q2.5", "english_primary"),
        _ans("q3.1", 20),  # invisible
        _ans("q3.2", 25),  # blends in
        _ans("q3.3", 60),
        _ans("q3.4", ["obscurity", "commoditization"]),
        _ans("q4.1", 50),
        _ans("q4.2", 50),
        _ans("q4.3", 50),
        _ans("q4.4", 50),
        _ans("q4.5", ["confident_peer", "respected_expert"]),
        _ans("q5.1", 60),
        _ans("q5.2", "category_leader"),
        _ans("q5.3", "trust"),
    ]


def _factors() -> list[PriorityFactor]:
    return [
        PriorityFactor(factor_name="A", how_addressed="…"),
        PriorityFactor(factor_name="B", how_addressed="…"),
    ]


def _register_all_module_responses(mock: MockLLMProvider, language: Language) -> None:
    """Set up the Mock to return a valid output for the narrative call
    plus every module's call. Outputs are content-shaped enough to pass
    Pydantic validation; quality is not what's being tested here."""
    mock.register_response(
        "PainNarrativeOutput",
        PainNarrativeOutput(
            language=language,
            narrative=(
                "TestBrand has earned the right shelf placement on quality but still hits "
                "sales calls cold — premium positioning is running ahead of recognition."
            ),
            priority_factors_addressed=_factors(),
        ),
    )
    mock.register_response(
        "StrategyThemeOutput",
        StrategyThemeOutput(
            language=language,
            theme="Quietly engineered for the Saudi business traveler who refuses to be loud.",
            elaboration="Substance over signal across every customer touchpoint.",
            priority_factors_addressed=_factors(),
        ),
    )
    mock.register_response(
        "ToneOutput",
        ToneOutput(
            language=language,
            descriptor="Quietly confident; assumes intelligence in the reader.",
            do_examples=[
                "Lead with the customer's situation.",
                "Stand by the work without bluster.",
                "Say what we mean in fewer words.",
            ],
            dont_examples=[
                "Don't say 'innovative solutions'.",
                "Don't open with we are passionate about.",
                "Don't use exclamation marks for emphasis.",
            ],
            priority_factors_addressed=_factors(),
        ),
    )
    mock.register_response(
        "NamingOutput",
        NamingOutput(
            language=language,
            candidates=[
                NameCandidate(
                    name="Sirr", rationale="Arabic root for 'essence'.", arabic_form="سِرّ"
                ),
                NameCandidate(name="North Reed", rationale="Direction + craft."),
                NameCandidate(
                    name="Beyat", rationale="Arabic root for 'home'.", arabic_form="بيات"
                ),
            ],
            priority_factors_addressed=_factors(),
        ),
    )
    mock.register_response(
        "SloganOutput",
        SloganOutput(
            language=language,
            options=[
                SloganOption(slogan="Build > Talk", rationale="Reinforces builder identity."),
                SloganOption(
                    slogan="Ship the truth", rationale="Pain alignment: action_misalignment."
                ),
            ],
            priority_factors_addressed=_factors(),
        ),
    )
    mock.register_response(
        "TaglineOutput",
        TaglineOutput(
            language=language,
            options=[
                TaglineOption(
                    tagline="Built to last, made to belong.",
                    rationale="Emotion: trust + belonging.",
                    intended_feeling="trust",
                ),
                TaglineOption(
                    tagline="Quiet strength, made here.",
                    rationale="Emotion: trust + cultural anchor.",
                    intended_feeling="trust",
                ),
            ],
            priority_factors_addressed=_factors(),
        ),
    )


async def test_full_session_flow_with_all_five_modules():
    # 1. Load real content
    bundle = load_content_bundle()

    # 2. Discovery answers
    answers = _full_session_fixture_answers()

    # 3. Rules engine + register resolver + brand DNA
    pain_categories = tag_pain_categories(
        answers, bundle.simple_rules, bundle.inferred_rules, bundle.pain_taxonomy
    )
    assert {c.id for c in pain_categories} >= {"obscurity", "commoditization"}

    session_id = uuid.uuid4()
    register = resolve_register(answers, bundle.register_rules, session_id)
    assert register.primary_language == Language.ENGLISH

    brand_dna_context = build_brand_dna_context(answers, bundle.questionnaire_en)

    # 4. Mock provider with all 6 responses (narrative + 5 modules)
    mock = MockLLMProvider()
    _register_all_module_responses(mock, register.primary_language)

    # 5. Run discovery's narrative generation
    pain_analysis, narrative_record = await generate_pain_narrative(
        brand_dna_context, pain_categories, register, session_id, mock
    )

    # 6. Decision Scope = all 5; build the plan
    scope = DecisionScope(
        session_id=session_id,
        modules={
            ModuleId.STRATEGY_THEME,
            ModuleId.TONE,
            ModuleId.NAMING,
            ModuleId.SLOGAN,
            ModuleId.TAGLINE,
        },
    )
    plan = build_execution_plan(scope)

    # 7. Run generation
    result = await run_generation(
        plan, brand_dna_context, pain_analysis, pain_categories, register, session_id, mock
    )

    # 8. End-to-end invariants
    assert len(result.module_outputs) == 5
    assert len(result.call_records) == 5
    assert mock.call_count == 6  # narrative + 5 modules

    # Canonical order (dict preserves insertion order)
    assert list(result.module_outputs.keys()) == [
        ModuleId.STRATEGY_THEME,
        ModuleId.TONE,
        ModuleId.NAMING,
        ModuleId.SLOGAN,
        ModuleId.TAGLINE,
    ]

    # Audit chain on every module output
    for output in result.module_outputs.values():
        assert output.session_id == session_id
        assert output.register_id == register.id
        assert output.language == register.primary_language
        assert len(output.llm_call_record_ids) == 1

    # Narrative also audit-tied
    assert pain_analysis.session_id == session_id
    assert pain_analysis.register_id == register.id
    assert pain_analysis.llm_call_record_ids == [narrative_record.id]

    # Upstream wiring per intersection rules: Tagline reads from Strategy + Tone
    tagline_out = result.module_outputs[ModuleId.TAGLINE]
    expected_tagline_upstream = {
        result.module_outputs[m].id for m in (ModuleId.STRATEGY_THEME, ModuleId.TONE)
    }
    assert set(tagline_out.upstream_module_outputs) == expected_tagline_upstream

    # Tone reads only from Strategy
    tone_out = result.module_outputs[ModuleId.TONE]
    assert tone_out.upstream_module_outputs == [result.module_outputs[ModuleId.STRATEGY_THEME].id]

    # Content shape: every module's content round-trips out via its Pydantic schema
    StrategyThemeOutput(**result.module_outputs[ModuleId.STRATEGY_THEME].content)
    ToneOutput(**result.module_outputs[ModuleId.TONE].content)
    NamingOutput(**result.module_outputs[ModuleId.NAMING].content)
    SloganOutput(**result.module_outputs[ModuleId.SLOGAN].content)
    TaglineOutput(**result.module_outputs[ModuleId.TAGLINE].content)
