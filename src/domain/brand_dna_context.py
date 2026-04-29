"""Brand DNA Context — typed contract for questionnaire-derived input to LLM consumers.

Used by the pain narrative generator (Discovery phase) and by every
module runner (Generation phase, Session 7+). The structure mirrors
the questionnaire sections (Identity, Audience, Voice, Aspiration)
and the band logic that converts raw slider values into 3-band
categorical signals (low / mid / high).

Per CLAUDE.md §2.4 every persisted LLM consumer needs structured
upstream context. This model is that structure — separate from
`LanguageRegister` (which has its own typed model), the typed pain
categories list (which the Rules Engine produces), and `session_id`
(a plain UUID).

Slider band convention: value < 40 → low, 40-60 inclusive → mid,
value > 60 → high. Each section's labels are domain-specific and
documented on the build helper.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from src.domain.questionnaire import Answer, AnswerMechanic, QuestionnaireVersion


class BrandInfo(BaseModel):
    """Identity-section context (Q1.1-Q1.4).

    Allowed `stage` values: starting / early / growing / established / mature.
    Allowed `position` values: pioneer / premium / challenger / specialist /
    accessible / traditional. `heritage_vs_vision_band` is one of
    heritage / balanced / vision derived from Q1.4's slider value.
    """

    model_config = ConfigDict(frozen=True)

    name: str
    description: str
    stage: str
    position: str
    heritage_vs_vision_band: str
    heritage_vs_vision_score: int = Field(..., ge=0, le=100)


class AudienceInfo(BaseModel):
    """Audience-section context (Q2.1-Q2.5).

    Bands: `age_band` younger/middle/older, `spend_band` value/mixed/aspirational,
    `decision_band` emotional/mixed/analytical. `language_preference` is one of
    arabic_only / arabic_primary / bilingual / english_primary / english_only.
    """

    model_config = ConfigDict(frozen=True)

    description: str
    age_band: str
    spend_band: str
    decision_band: str
    language_preference: str


class VoiceInfo(BaseModel):
    """Voice-section context (Q4.1-Q4.5).

    Bands: `formality_band` casual/semi_formal/formal,
    `warmth_band` cool/balanced/warm, `confidence_band` quiet/balanced/bold,
    `energy_band` calm/balanced/dynamic. `characters` is the Q4.5 multi-choice
    list (1-2 selections per the questionnaire's max_selections).
    """

    model_config = ConfigDict(frozen=True)

    formality_band: str
    warmth_band: str
    confidence_band: str
    energy_band: str
    characters: list[str] = Field(..., min_length=1, max_length=2)


class AspirationInfo(BaseModel):
    """Aspiration-section context (Q5.1-Q5.4).

    `posture_band` defending/balanced/reinventing. `three_year` and
    `emotion_target` are the raw Q5.2 / Q5.3 option values.
    `brand_premise` is the optional Q5.4 free text — empty string if
    the user did not answer.
    """

    model_config = ConfigDict(frozen=True)

    posture_band: str
    three_year: str
    emotion_target: str
    brand_premise: str


class PainHints(BaseModel):
    """Raw pain-related answers passed alongside the rules-derived pain categories.

    The tagged pain categories (typed `list[PainCategory]`) come from the
    Rules Engine and are passed to LLM consumers separately. This model
    carries the raw Q3.4 multi-choice selections so prompts can reference
    what the brand owner *said* alongside what the rules derived.
    """

    model_config = ConfigDict(frozen=True)

    top_frustrations: list[str]


class BrandDNAContext(BaseModel):
    """Complete questionnaire-derived context fed to every LLM consumer.

    Pain categories, register, and session metadata are passed alongside
    this model. They have their own typed representations
    (`list[PainCategory]`, `LanguageRegister`, `UUID`) and don't belong
    inside `BrandDNAContext`.
    """

    model_config = ConfigDict(frozen=True)

    brand: BrandInfo
    audience: AudienceInfo
    voice: VoiceInfo
    aspiration: AspirationInfo
    pain: PainHints


# ---------------------------------------------------------------------------
# Build helper
# ---------------------------------------------------------------------------


def _slider_band(value: int, low_label: str, mid_label: str, high_label: str) -> str:
    """Bucket a 0-100 slider value into a 3-band categorical signal.

    Convention: value < 40 → low, 40-60 inclusive → mid, value > 60 → high.
    """
    if value < 40:
        return low_label
    if value > 60:
        return high_label
    return mid_label


def _split_brand_name_and_description(q11_text: str) -> tuple[str, str]:
    """Split Q1.1's combined answer into (name, description).

    The questionnaire asks "What's your brand name? In one sentence, what
    does your brand do?" — most users answer in a "BrandName. Description."
    shape. We split on the first ". " separator. If no separator exists,
    name and description are both the full Q1.1 text (Session 8's session
    creation flow can override the name explicitly).
    """
    parts = q11_text.split(". ", 1)
    if len(parts) == 2 and parts[0].strip() and parts[1].strip():
        return parts[0].strip(), parts[1].strip()
    return q11_text, q11_text


def _required(answers_by_id: dict[str, str | int | list[str]], qid: str) -> str | int | list[str]:
    if qid not in answers_by_id:
        raise ValueError(f"Required answer missing: {qid}")
    return answers_by_id[qid]


def build_brand_dna_context(
    answers: list[Answer],
    questionnaire: QuestionnaireVersion,
) -> BrandDNAContext:
    """Assemble a `BrandDNAContext` from raw answers and questionnaire metadata.

    The `questionnaire` parameter is currently used only as the static
    schema reference (e.g., to look up the mechanic of a question if
    needed); the helper does not validate that every required question
    in the questionnaire has been answered — that is the Questionnaire
    Service's job. This helper raises `ValueError` only when a specific
    answer that BrandDNAContext requires is missing.

    Slider band mappings (raw question_id → low/mid/high label tuple):
      Q1.4 heritage_vs_vision: heritage / balanced / vision
      Q2.2 audience age:       younger / middle / older
      Q2.3 spending mindset:   value / mixed / aspirational
      Q2.4 decision style:     emotional / mixed / analytical
      Q4.1 formality:          casual / semi_formal / formal
      Q4.2 warmth:             cool / balanced / warm
      Q4.3 confidence:         quiet / balanced / bold
      Q4.4 energy:             calm / balanced / dynamic
      Q5.1 posture:            defending / balanced / reinventing
    """
    by_id: dict[str, str | int | list[str]] = {a.question_id: a.value for a in answers}

    # Identity
    q11 = _required(by_id, "q1.1")
    if not isinstance(q11, str):
        raise ValueError("Q1.1 must be a free-text str answer")
    name, description = _split_brand_name_and_description(q11)

    stage = _required(by_id, "q1.2")
    position = _required(by_id, "q1.3")
    heritage_score = _required(by_id, "q1.4")
    if not isinstance(heritage_score, int):
        raise ValueError("Q1.4 must be a slider int answer")

    brand = BrandInfo(
        name=name,
        description=description,
        stage=str(stage),
        position=str(position),
        heritage_vs_vision_band=_slider_band(heritage_score, "heritage", "balanced", "vision"),
        heritage_vs_vision_score=heritage_score,
    )

    # Audience
    q21 = _required(by_id, "q2.1")
    q22 = _required(by_id, "q2.2")
    q23 = _required(by_id, "q2.3")
    q24 = _required(by_id, "q2.4")
    q25 = _required(by_id, "q2.5")

    audience = AudienceInfo(
        description=str(q21),
        age_band=_slider_band(int(q22), "younger", "middle", "older"),
        spend_band=_slider_band(int(q23), "value", "mixed", "aspirational"),
        decision_band=_slider_band(int(q24), "emotional", "mixed", "analytical"),
        language_preference=str(q25),
    )

    # Voice
    q41 = _required(by_id, "q4.1")
    q42 = _required(by_id, "q4.2")
    q43 = _required(by_id, "q4.3")
    q44 = _required(by_id, "q4.4")
    q45 = _required(by_id, "q4.5")
    if not isinstance(q45, list):
        raise ValueError("Q4.5 must be a multi-choice list answer")

    voice = VoiceInfo(
        formality_band=_slider_band(int(q41), "casual", "semi_formal", "formal"),
        warmth_band=_slider_band(int(q42), "cool", "balanced", "warm"),
        confidence_band=_slider_band(int(q43), "quiet", "balanced", "bold"),
        energy_band=_slider_band(int(q44), "calm", "balanced", "dynamic"),
        characters=[str(c) for c in q45],
    )

    # Aspiration
    q51 = _required(by_id, "q5.1")
    q52 = _required(by_id, "q5.2")
    q53 = _required(by_id, "q5.3")
    q54 = by_id.get("q5.4", "")  # optional

    aspiration = AspirationInfo(
        posture_band=_slider_band(int(q51), "defending", "balanced", "reinventing"),
        three_year=str(q52),
        emotion_target=str(q53),
        brand_premise=str(q54) if q54 is not None else "",
    )

    # Pain hints (Q3.4)
    q34 = by_id.get("q3.4", [])
    if not isinstance(q34, list):
        raise ValueError("Q3.4 must be a multi-choice list answer")
    pain = PainHints(top_frustrations=[str(f) for f in q34])

    # The questionnaire parameter is currently informational; once question-
    # mechanic-driven validation lands (Session 7+), this helper can use it
    # to confirm that, e.g., q4.1 is a SLIDER mechanic before treating its
    # value as int. Silence the unused-arg lint without losing the parameter.
    _ = questionnaire.questions if questionnaire else None
    _ = AnswerMechanic  # imported for future use; intentional pin

    return BrandDNAContext(
        brand=brand,
        audience=audience,
        voice=voice,
        aspiration=aspiration,
        pain=pain,
    )
