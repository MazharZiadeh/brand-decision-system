"""Language Register Resolver.

Pure-logic deterministic component per CLAUDE.md §2.5 — register is
derived from answers, never operator-configured. Walks the four
sections of `register_rules.yaml` in order; first matching condition
in each section wins (with `default` as fallback). Cultural anchors
are aggregated from every always-on entry plus every matching
condition.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from src.discovery.condition_evaluator import evaluate_condition
from src.discovery.exceptions import DiscoveryError
from src.domain.language import Language
from src.domain.questionnaire import Answer
from src.domain.register import ArabicVariety, LanguageRegister, RegisterLevel


def resolve_register(
    answers: list[Answer],
    register_rules: dict[str, Any],
    session_id: uuid.UUID,
) -> LanguageRegister:
    """Resolve a `LanguageRegister` from answers using the loaded rules."""
    rules = register_rules["register_rules"]

    primary_language = _resolve_first_match(
        rules["primary_language"],
        answers,
        value_field="primary_language",
        default="en",
    )
    arabic_variety = _resolve_first_match(
        rules["arabic_variety"],
        answers,
        value_field="arabic_variety",
        default="not_applicable",
    )
    register_level = _resolve_first_match(
        rules["register_level"],
        answers,
        value_field="register_level",
        default="semi_formal",
    )
    cultural_anchors = _resolve_cultural_anchors(rules["cultural_anchors"], answers)

    return LanguageRegister(
        id=uuid.uuid4(),
        session_id=session_id,
        primary_language=Language(primary_language),
        arabic_variety=ArabicVariety(arabic_variety),
        register_level=RegisterLevel(register_level),
        cultural_anchors=cultural_anchors,
        derived_at=datetime.now(UTC),
    )


def _resolve_first_match(
    section_entries: list[dict[str, Any]],
    answers: list[Answer],
    *,
    value_field: str,
    default: str,
) -> str:
    """Walk an ordered list of {condition, sets} entries plus an optional
    {default: {...}} entry; return the value of `value_field` from the
    first match. Falls back to `default` if no entry matches and no
    default is declared in the YAML.
    """
    declared_default: str | None = None
    for entry in section_entries:
        if "default" in entry:
            declared_default = entry["default"].get(value_field, declared_default)
            continue
        if "condition" not in entry or "sets" not in entry:
            raise DiscoveryError(
                f"register_rules entry missing required keys (condition, sets): {entry}"
            )
        if evaluate_condition(entry["condition"], answers):
            value = entry["sets"].get(value_field)
            if value is None:
                raise DiscoveryError(
                    f"register_rules entry's `sets` block has no `{value_field}`: {entry}"
                )
            return value
    return declared_default if declared_default is not None else default


def _resolve_cultural_anchors(
    section_entries: list[dict[str, Any]],
    answers: list[Answer],
) -> list[str]:
    """Aggregate anchors across always-on entries and every matching
    condition. Order is preserved (always entries first, then matches in
    YAML order) and duplicates are dropped while keeping first occurrence.
    """
    seen: dict[str, None] = {}  # ordered set
    for entry in section_entries:
        if "always" in entry:
            for anchor in entry["always"]:
                seen.setdefault(anchor, None)
            continue
        if "condition" in entry and "adds" in entry:
            if evaluate_condition(entry["condition"], answers):
                for anchor in entry["adds"]:
                    seen.setdefault(anchor, None)
            continue
        raise DiscoveryError(
            f"cultural_anchors entry must have either `always` or `condition + adds`: {entry}"
        )
    return list(seen.keys())
