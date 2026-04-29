"""Prompt builder — turns Discovery context + scope state into a rendered prompt.

For a given target module, the builder:
1. Looks up the module's Jinja2 template via `MODULE_REGISTRY`.
2. Loads the Jinja2 environment with `StrictUndefined` so any missing
   template variable fails loud at render time rather than producing a
   silently-empty section in production.
3. Assembles the `pain` dict (flat-shape categories tuned for the
   `unified_preamble.j2` access pattern, plus the narrative from
   `PainAnalysis` and the brand owner's selected top frustrations).
4. Computes the upstream outputs available right now and unwraps each
   one's `ModuleOutput.content` for template access — so templates can
   write `{{ upstream.strategy_theme.theme }}` without going through
   `.content`.
5. Renders and returns the string.

Per CLAUDE.md §2.1 this module is pure-logic; no LLM imports, no I/O
beyond reading templates from disk at module-import time.
"""

from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined

from src.domain.brand_dna_context import BrandDNAContext
from src.domain.language import Language
from src.domain.module import ModuleId, ModuleOutput
from src.domain.pain import PainAnalysis, PainCategory
from src.domain.register import LanguageRegister
from src.generation.registry import get_module_config
from src.generation.upstream import build_upstream_outputs

_PROMPT_DIR = Path(__file__).resolve().parents[2] / "content" / "prompts"
_env = Environment(
    loader=FileSystemLoader(str(_PROMPT_DIR)),
    undefined=StrictUndefined,
    autoescape=False,
    keep_trailing_newline=True,
)


def _project_pain_categories(
    categories: list[PainCategory],
    language: Language,
) -> list[dict[str, str]]:
    """Project bilingual `PainCategory`s into the flat shape that
    `unified_preamble.j2` expects: `{id, name, description}` with name
    and description picked by `language`. Falls back to the category id
    if the chosen language is missing on a content object.
    """
    return [
        {
            "id": c.id,
            "name": c.name_by_language.get(language, c.id),
            "description": c.description_by_language.get(language, ""),
        }
        for c in categories
    ]


def build_module_prompt(
    target_module: ModuleId,
    brand_dna_context: BrandDNAContext,
    pain_analysis: PainAnalysis,
    pain_categories: list[PainCategory],
    register: LanguageRegister,
    completed_outputs: dict[ModuleId, ModuleOutput],
    scope_modules: set[ModuleId],
) -> str:
    """Render the full prompt (preamble + module extension) for `target_module`."""
    config = get_module_config(target_module)
    template = _env.get_template(config.template_path)

    upstream_models = build_upstream_outputs(target_module, completed_outputs, scope_modules)
    # Templates access {{ upstream.strategy_theme.theme }} — they expect the
    # content dict, not the wrapping ModuleOutput. Un-completed slots stay
    # None so `{% if upstream.X %}` stays safe under StrictUndefined.
    upstream = {
        key: (out.content if out is not None else None) for key, out in upstream_models.items()
    }

    pain = {
        "tagged_categories": _project_pain_categories(pain_categories, register.primary_language),
        "narrative": pain_analysis.narrative,
        "top_frustrations": brand_dna_context.pain.top_frustrations,
    }

    return template.render(
        brand=brand_dna_context.brand,
        audience=brand_dna_context.audience,
        voice=brand_dna_context.voice,
        aspiration=brand_dna_context.aspiration,
        pain=pain,
        register=register,
        upstream=upstream,
    )
