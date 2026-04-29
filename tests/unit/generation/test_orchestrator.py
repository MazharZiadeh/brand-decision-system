"""Tests for the generation orchestrator."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest

from src.domain.brand_dna_context import (
    AspirationInfo,
    AudienceInfo,
    BrandDNAContext,
    BrandInfo,
    PainHints,
    VoiceInfo,
)
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
from src.domain.pain import PainAnalysis, PainCategory
from src.domain.rationale import PriorityFactor
from src.domain.register import ArabicVariety, LanguageRegister, RegisterLevel
from src.generation.exceptions import GenerationError
from src.generation.orchestrator import GenerationResult, run_generation
from src.llm.exceptions import LLMTimeoutError
from src.llm.mock import MockLLMProvider
from src.orchestration.engine import build_execution_plan


def _factors() -> list[PriorityFactor]:
    return [
        PriorityFactor(factor_name="A", how_addressed="…"),
        PriorityFactor(factor_name="B", how_addressed="…"),
    ]


def _ctx() -> BrandDNAContext:
    return BrandDNAContext(
        brand=BrandInfo(
            name="TestBrand",
            description="…",
            stage="early",
            position="premium",
            heritage_vs_vision_band="balanced",
            heritage_vs_vision_score=50,
        ),
        audience=AudienceInfo(
            description="…",
            age_band="middle",
            spend_band="aspirational",
            decision_band="mixed",
            language_preference="english_primary",
        ),
        voice=VoiceInfo(
            formality_band="semi_formal",
            warmth_band="warm",
            confidence_band="balanced",
            energy_band="balanced",
            characters=["confident_peer"],
        ),
        aspiration=AspirationInfo(
            posture_band="balanced",
            three_year="category_leader",
            emotion_target="trust",
            brand_premise="",
        ),
        pain=PainHints(top_frustrations=["obscurity"]),
    )


def _category(cid: str = "obscurity") -> PainCategory:
    return PainCategory(
        id=cid,
        name_by_language={Language.ENGLISH: cid.title(), Language.ARABIC: cid},
        description_by_language={
            Language.ENGLISH: f"{cid} description",
            Language.ARABIC: f"وصف {cid}",
        },
    )


def _register(session_id: uuid.UUID) -> LanguageRegister:
    return LanguageRegister(
        session_id=session_id,
        primary_language=Language.ENGLISH,
        arabic_variety=ArabicVariety.NOT_APPLICABLE,
        register_level=RegisterLevel.SEMI_FORMAL,
        cultural_anchors=["saudi_market_context", "premium_positioning"],
        derived_at=datetime.now(UTC),
    )


def _pain_analysis(session_id: uuid.UUID, register_id: uuid.UUID) -> PainAnalysis:
    return PainAnalysis(
        session_id=session_id,
        register_id=register_id,
        tagged_pain_categories=["obscurity"],
        narrative="The brand is invisible to its target audience despite premium positioning.",
        rationale_id=uuid.uuid4(),
        llm_call_record_ids=[uuid.uuid4()],
        language=Language.ENGLISH,
    )


def _all_module_outputs() -> dict[str, object]:
    return {
        "StrategyThemeOutput": StrategyThemeOutput(
            language=Language.ENGLISH,
            theme="Quietly engineered.",
            elaboration="Substance over signal across every customer touchpoint.",
            priority_factors_addressed=_factors(),
        ),
        "ToneOutput": ToneOutput(
            language=Language.ENGLISH,
            descriptor="Quietly confident.",
            do_examples=["one", "two", "three"],
            dont_examples=["a", "b", "c"],
            priority_factors_addressed=_factors(),
        ),
        "NamingOutput": NamingOutput(
            language=Language.ENGLISH,
            candidates=[
                NameCandidate(name="A", rationale="…"),
                NameCandidate(name="B", rationale="…"),
                NameCandidate(name="C", rationale="…"),
            ],
            priority_factors_addressed=_factors(),
        ),
        "SloganOutput": SloganOutput(
            language=Language.ENGLISH,
            options=[
                SloganOption(slogan="X", rationale="…"),
                SloganOption(slogan="Y", rationale="…"),
            ],
            priority_factors_addressed=_factors(),
        ),
        "TaglineOutput": TaglineOutput(
            language=Language.ENGLISH,
            options=[
                TaglineOption(tagline="P", rationale="…", intended_feeling="trust"),
                TaglineOption(tagline="Q", rationale="…", intended_feeling="trust"),
            ],
            priority_factors_addressed=_factors(),
        ),
    }


def _provider_with_all_responses() -> MockLLMProvider:
    p = MockLLMProvider()
    for name, instance in _all_module_outputs().items():
        p.register_response(name, instance)
    return p


# ── single-module scopes ───────────────────────────────────────────


async def test_run_generation_with_strategy_only_produces_one_output():
    sid = uuid.uuid4()
    register = _register(sid)
    scope = DecisionScope(session_id=sid, modules={ModuleId.STRATEGY_THEME})
    plan = build_execution_plan(scope)

    result = await run_generation(
        plan,
        _ctx(),
        _pain_analysis(sid, register.id),
        [_category()],
        register,
        sid,
        _provider_with_all_responses(),
    )
    assert isinstance(result, GenerationResult)
    assert len(result.module_outputs) == 1
    assert ModuleId.STRATEGY_THEME in result.module_outputs
    assert len(result.call_records) == 1


# ── full scope: 5 outputs in canonical order ──────────────────────


async def test_run_generation_with_all_five_modules_produces_five_outputs_in_canonical_order():
    sid = uuid.uuid4()
    register = _register(sid)
    scope = DecisionScope(session_id=sid, modules=set(ModuleId))
    plan = build_execution_plan(scope)

    result = await run_generation(
        plan,
        _ctx(),
        _pain_analysis(sid, register.id),
        [_category()],
        register,
        sid,
        _provider_with_all_responses(),
    )
    assert len(result.module_outputs) == 5
    assert list(result.module_outputs.keys()) == [
        ModuleId.STRATEGY_THEME,
        ModuleId.TONE,
        ModuleId.NAMING,
        ModuleId.SLOGAN,
        ModuleId.TAGLINE,
    ]
    assert len(result.call_records) == 5


async def test_run_generation_call_records_in_call_order():
    sid = uuid.uuid4()
    register = _register(sid)
    plan = build_execution_plan(DecisionScope(session_id=sid, modules=set(ModuleId)))
    result = await run_generation(
        plan,
        _ctx(),
        _pain_analysis(sid, register.id),
        [_category()],
        register,
        sid,
        _provider_with_all_responses(),
    )
    output_ids_in_order = [result.module_outputs[m].id for m in result.module_outputs]
    record_module_order = [r.module for r in result.call_records]
    assert record_module_order == list(result.module_outputs.keys())
    assert len(output_ids_in_order) == 5


# ── upstream wiring ──────────────────────────────────────────────


async def test_run_generation_passes_upstream_to_module_runner():
    sid = uuid.uuid4()
    register = _register(sid)
    plan = build_execution_plan(
        DecisionScope(session_id=sid, modules={ModuleId.STRATEGY_THEME, ModuleId.TONE})
    )
    result = await run_generation(
        plan,
        _ctx(),
        _pain_analysis(sid, register.id),
        [_category()],
        register,
        sid,
        _provider_with_all_responses(),
    )
    tone_out = result.module_outputs[ModuleId.TONE]
    strategy_out = result.module_outputs[ModuleId.STRATEGY_THEME]
    assert tone_out.upstream_module_outputs == [strategy_out.id]


async def test_run_generation_intersection_specific_subset():
    """Strategy + Tagline only: Tagline's upstream contains Strategy
    via the (STRATEGY → TAGLINE) intersection pair, no Tone."""
    sid = uuid.uuid4()
    register = _register(sid)
    plan = build_execution_plan(
        DecisionScope(session_id=sid, modules={ModuleId.STRATEGY_THEME, ModuleId.TAGLINE})
    )
    result = await run_generation(
        plan,
        _ctx(),
        _pain_analysis(sid, register.id),
        [_category()],
        register,
        sid,
        _provider_with_all_responses(),
    )
    tagline_out = result.module_outputs[ModuleId.TAGLINE]
    strategy_out = result.module_outputs[ModuleId.STRATEGY_THEME]
    assert tagline_out.upstream_module_outputs == [strategy_out.id]


# ── audit chain propagation ──────────────────────────────────────


async def test_run_generation_register_id_propagates_to_every_output():
    sid = uuid.uuid4()
    register = _register(sid)
    plan = build_execution_plan(DecisionScope(session_id=sid, modules=set(ModuleId)))
    result = await run_generation(
        plan,
        _ctx(),
        _pain_analysis(sid, register.id),
        [_category()],
        register,
        sid,
        _provider_with_all_responses(),
    )
    for output in result.module_outputs.values():
        assert output.register_id == register.id


async def test_run_generation_session_id_propagates_to_every_output_and_call_record():
    sid = uuid.uuid4()
    register = _register(sid)
    plan = build_execution_plan(DecisionScope(session_id=sid, modules=set(ModuleId)))
    result = await run_generation(
        plan,
        _ctx(),
        _pain_analysis(sid, register.id),
        [_category()],
        register,
        sid,
        _provider_with_all_responses(),
    )
    for output in result.module_outputs.values():
        assert output.session_id == sid
    for record in result.call_records:
        assert record.session_id == sid


# ── partial-failure handling ─────────────────────────────────────


async def test_run_generation_partial_failure_raises_with_progress():
    """Strategy succeeds, Tone fails → GenerationError carries Strategy's
    output and the call record from BOTH the success and the failure."""
    sid = uuid.uuid4()
    register = _register(sid)
    plan = build_execution_plan(
        DecisionScope(session_id=sid, modules={ModuleId.STRATEGY_THEME, ModuleId.TONE})
    )

    # Provider returns Strategy successfully, then errors on the Tone call.
    provider = MockLLMProvider()
    provider.register_response("StrategyThemeOutput", _all_module_outputs()["StrategyThemeOutput"])
    # Tone has no registration AND we inject an error; injection takes effect on
    # the second call (Strategy is the first).

    # We need a provider that succeeds for the first call and fails on the second.
    # Inject the error AFTER the first call; do this via a custom subclass-free hook:
    # use a wrapper that calls the underlying provider but injects on the 2nd call.
    class _SecondCallFails(MockLLMProvider):
        async def call(self, request, output_schema):  # type: ignore[override]
            if self.call_count == 0 or request.module == ModuleId.STRATEGY_THEME:
                return await super().call(request, output_schema)
            self.inject_error(LLMTimeoutError("simulated tone failure"))
            return await super().call(request, output_schema)

    sub = _SecondCallFails()
    sub.register_response("StrategyThemeOutput", _all_module_outputs()["StrategyThemeOutput"])

    with pytest.raises(GenerationError) as ei:
        await run_generation(
            plan,
            _ctx(),
            _pain_analysis(sid, register.id),
            [_category()],
            register,
            sid,
            sub,
        )
    err = ei.value
    assert ModuleId.STRATEGY_THEME in err.completed_outputs
    assert ModuleId.TONE not in err.completed_outputs
    # We collected the Strategy success record AND the Tone failure record.
    assert len(err.call_records_so_far) >= 1
    assert isinstance(err.original_exception, LLMTimeoutError)
