"""YAML content loader.

Loads all 5 content files at startup, validates each against its domain
model (or against the structural shape the Rules Engine / Register
Resolver consume), and returns a `ContentBundle`. Any failure raises
`ContentLoadError` so the app refuses to start with miscalibrated
content per CLAUDE.md §5.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from src.discovery.content_bundle import ContentBundle
from src.discovery.exceptions import ContentLoadError
from src.domain.pain import PainTaxonomy, Rule
from src.domain.questionnaire import QuestionnaireVersion

CONTENT_ROOT = Path(__file__).resolve().parents[2] / "content"
QUESTIONNAIRE_VERSION_DIR = CONTENT_ROOT / "questionnaires" / "v0.1.0"


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ContentLoadError(f"Required content file not found: {path}")
    try:
        with path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ContentLoadError(f"Malformed YAML in {path.name}: {e}") from e
    if not isinstance(data, dict):
        raise ContentLoadError(
            f"Top-level YAML in {path.name} must be a mapping; got {type(data).__name__}"
        )
    return data


def _build_questionnaire(path: Path) -> QuestionnaireVersion:
    try:
        return QuestionnaireVersion(**_load_yaml(path))
    except ValidationError as e:
        raise ContentLoadError(f"Questionnaire validation failed for {path.name}: {e}") from e


def _build_pain_taxonomy(path: Path) -> PainTaxonomy:
    try:
        return PainTaxonomy(**_load_yaml(path))
    except ValidationError as e:
        raise ContentLoadError(f"Pain taxonomy validation failed: {e}") from e


def _build_rules(path: Path) -> tuple[list[Rule], list[dict[str, Any]]]:
    data = _load_yaml(path)
    if "rules" not in data:
        raise ContentLoadError(f"{path.name} is missing top-level `rules` block")
    if "inferred_rules" not in data:
        raise ContentLoadError(f"{path.name} is missing top-level `inferred_rules` block")
    try:
        simple = [Rule(**r) for r in data["rules"]]
    except ValidationError as e:
        raise ContentLoadError(f"Pain rules validation failed: {e}") from e
    inferred = list(data["inferred_rules"])
    for entry in inferred:
        if "trigger" not in entry or "pain_category_id" not in entry:
            raise ContentLoadError(
                f"Inferred rule missing required keys (trigger, pain_category_id): {entry}"
            )
    return simple, inferred


def _build_register_rules(path: Path) -> dict[str, Any]:
    data = _load_yaml(path)
    if "register_rules" not in data:
        raise ContentLoadError(f"{path.name} is missing top-level `register_rules` block")
    rules = data["register_rules"]
    expected = {"primary_language", "arabic_variety", "register_level", "cultural_anchors"}
    missing = expected - set(rules.keys())
    if missing:
        raise ContentLoadError(f"register_rules missing sections: {sorted(missing)}")
    return data


def load_content_bundle(content_root: Path | None = None) -> ContentBundle:
    """Load and validate all v0.1 content. Raises ContentLoadError on any failure.

    `content_root` overrides the default `content/` location. Tests can point
    this at a `tmp_path` to exercise error paths without disturbing real content.
    """
    root = content_root or CONTENT_ROOT
    qv_dir = root / "questionnaires" / "v0.1.0"

    questionnaire_en = _build_questionnaire(qv_dir / "questionnaire.en.yaml")
    questionnaire_ar = _build_questionnaire(qv_dir / "questionnaire.ar.yaml")
    pain_taxonomy = _build_pain_taxonomy(root / "pain_taxonomy.yaml")
    simple_rules, inferred_rules = _build_rules(root / "pain_rules.yaml")
    register_rules = _build_register_rules(root / "register_rules.yaml")

    return ContentBundle(
        questionnaire_en=questionnaire_en,
        questionnaire_ar=questionnaire_ar,
        pain_taxonomy=pain_taxonomy,
        simple_rules=simple_rules,
        inferred_rules=inferred_rules,
        register_rules=register_rules,
    )
