import uuid
from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from src.domain.language import Language, LanguageTagged


class AnswerMechanic(StrEnum):
    """The kinds of answer captured by a question."""

    SLIDER = "slider"
    SINGLE_CHOICE = "single_choice"
    MULTI_CHOICE = "multi_choice"
    FREE_TEXT = "free_text"
    RANKING = "ranking"
    BRANCHING = "branching"


class AnswerOption(BaseModel):
    """One discrete option for a single- or multi-choice question."""

    model_config = ConfigDict(frozen=True)

    value: str
    label_by_language: dict[Language, str]


class SliderConfig(BaseModel):
    """Slider mechanics: range plus left/right (and optional midpoint) labels per language."""

    model_config = ConfigDict(frozen=True)

    min_value: int = 0
    max_value: int = 100
    left_label_by_language: dict[Language, str]
    right_label_by_language: dict[Language, str]
    midpoint_label_by_language: dict[Language, str] | None = None


class Question(BaseModel):
    """One question in the canonical questionnaire.

    Each Question carries its text in BOTH languages via `text_by_language`,
    rather than itself being language-tagged. The Answer that responds to a
    Question is the language-tagged content object.
    """

    model_config = ConfigDict(frozen=True)

    id: str
    section: str
    text_by_language: dict[Language, str]
    mechanic: AnswerMechanic
    options: list[AnswerOption] | None = None
    slider_config: SliderConfig | None = None
    branching_rule: str | None = None
    required: bool = True


class QuestionnaireVersion(BaseModel):
    """Immutable expert-authored version of questionnaire content.

    Once created, the version is fixed: any change produces a new version with
    a new id and content_hash. Sessions stamp the version they were run against.
    """

    model_config = ConfigDict(frozen=True)

    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    version: str
    content_hash: str
    questions: list[Question]
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class Answer(LanguageTagged):
    """A single captured response to a Question.

    Per CLAUDE.md §2.4, `language` is required — the language the answer was
    given in. The `value` shape depends on the question's mechanic:
    - SLIDER → int
    - SINGLE_CHOICE / FREE_TEXT → str
    - MULTI_CHOICE / RANKING → list[str]
    Mechanic-consistency is enforced upstream by the Questionnaire Service,
    not here, because Answer doesn't carry the Question's mechanic.
    """

    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    question_id: str
    value: str | int | list[str]
    submitted_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class QuestionnaireInstance(BaseModel):
    """Captured answers for one session, stamped with the QuestionnaireVersion used."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    session_id: uuid.UUID
    questionnaire_version_id: uuid.UUID
    answers: list[Answer] = Field(default_factory=list)
    completed_at: datetime | None = None
