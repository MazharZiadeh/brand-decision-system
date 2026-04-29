"""Loader tests: happy path against real content + error paths via tmp_path."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from src.discovery.content_bundle import ContentBundle
from src.discovery.exceptions import ContentLoadError
from src.discovery.loader import CONTENT_ROOT, load_content_bundle

# ── Happy-path tests against the real v0.1 content ───────────────────


def test_load_content_bundle_succeeds_with_real_content():
    bundle = load_content_bundle()
    assert isinstance(bundle, ContentBundle)
    assert bundle.questionnaire_en is not None
    assert bundle.questionnaire_ar is not None
    assert bundle.pain_taxonomy is not None
    assert bundle.simple_rules
    assert bundle.inferred_rules
    assert bundle.register_rules


def test_loader_returns_22_questions_per_questionnaire():
    bundle = load_content_bundle()
    assert len(bundle.questionnaire_en.questions) == 22
    assert len(bundle.questionnaire_ar.questions) == 22


def test_loader_finds_10_pain_categories():
    bundle = load_content_bundle()
    assert len(bundle.pain_taxonomy.categories) == 10


def test_loader_returns_at_least_13_simple_rules():
    bundle = load_content_bundle()
    assert len(bundle.simple_rules) >= 13


def test_loader_inferred_rules_block_present():
    bundle = load_content_bundle()
    assert len(bundle.inferred_rules) >= 1
    for entry in bundle.inferred_rules:
        assert "trigger" in entry
        assert "pain_category_id" in entry


def test_loader_register_rules_has_all_four_sections():
    bundle = load_content_bundle()
    rules = bundle.register_rules["register_rules"]
    assert "primary_language" in rules
    assert "arabic_variety" in rules
    assert "register_level" in rules
    assert "cultural_anchors" in rules


# ── Error-path tests using tmp_path ──────────────────────────────────


@pytest.fixture
def fake_content_root(tmp_path: Path) -> Path:
    """Copy the real content tree into tmp_path so tests can mutate it."""
    dest = tmp_path / "content"
    shutil.copytree(CONTENT_ROOT, dest)
    return dest


def test_loader_raises_on_missing_file(fake_content_root: Path):
    (fake_content_root / "pain_taxonomy.yaml").unlink()
    with pytest.raises(ContentLoadError) as ei:
        load_content_bundle(content_root=fake_content_root)
    assert "pain_taxonomy.yaml" in str(ei.value)


def test_loader_raises_on_malformed_yaml(fake_content_root: Path):
    (fake_content_root / "pain_taxonomy.yaml").write_text(
        "not: valid:\n  - yaml: [unclosed",
        encoding="utf-8",
    )
    with pytest.raises(ContentLoadError) as ei:
        load_content_bundle(content_root=fake_content_root)
    assert "Malformed YAML" in str(ei.value)


def test_loader_raises_on_pydantic_validation_failure(fake_content_root: Path):
    # Strip the required `version` field — Pydantic should reject.
    (fake_content_root / "pain_taxonomy.yaml").write_text(
        "categories: []\n",
        encoding="utf-8",
    )
    with pytest.raises(ContentLoadError) as ei:
        load_content_bundle(content_root=fake_content_root)
    assert "Pain taxonomy validation failed" in str(ei.value)


def test_loader_raises_when_pain_rules_missing_inferred_block(fake_content_root: Path):
    (fake_content_root / "pain_rules.yaml").write_text(
        "rules: []\n",
        encoding="utf-8",
    )
    with pytest.raises(ContentLoadError) as ei:
        load_content_bundle(content_root=fake_content_root)
    assert "inferred_rules" in str(ei.value)


def test_loader_raises_when_register_rules_missing_section(fake_content_root: Path):
    (fake_content_root / "register_rules.yaml").write_text(
        "register_rules:\n  primary_language: []\n",
        encoding="utf-8",
    )
    with pytest.raises(ContentLoadError) as ei:
        load_content_bundle(content_root=fake_content_root)
    assert "missing sections" in str(ei.value)
