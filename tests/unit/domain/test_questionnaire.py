import uuid

import pytest
from pydantic import ValidationError

from src.domain.language import Language
from src.domain.questionnaire import (
    Answer,
    AnswerMechanic,
    AnswerOption,
    Question,
    QuestionnaireInstance,
    QuestionnaireVersion,
    SliderConfig,
)


def _slider_question() -> Question:
    return Question(
        id="q1.1",
        section="identity",
        text_by_language={
            Language.ENGLISH: "Heritage or vision?",
            Language.ARABIC: "إرث أم رؤية؟",
        },
        mechanic=AnswerMechanic.SLIDER,
        slider_config=SliderConfig(
            left_label_by_language={Language.ENGLISH: "All heritage", Language.ARABIC: "إرث"},
            right_label_by_language={Language.ENGLISH: "All vision", Language.ARABIC: "رؤية"},
        ),
    )


def test_valid_question():
    q = _slider_question()
    assert q.id == "q1.1"
    assert q.required is True


def test_question_is_frozen():
    q = _slider_question()
    with pytest.raises(ValidationError):
        q.id = "different"  # type: ignore[misc]


def test_answer_option_is_frozen():
    o = AnswerOption(
        value="pioneer",
        label_by_language={Language.ENGLISH: "Pioneer", Language.ARABIC: "رائد"},
    )
    with pytest.raises(ValidationError):
        o.value = "x"  # type: ignore[misc]


def test_questionnaire_version_is_frozen():
    v = QuestionnaireVersion(
        version="1.0.0",
        content_hash="deadbeef",
        questions=[_slider_question()],
    )
    with pytest.raises(ValidationError):
        v.version = "2.0.0"  # type: ignore[misc]


def test_answer_requires_language():
    with pytest.raises(ValidationError):
        Answer(question_id="q1.1", value=42)  # type: ignore[call-arg]


def test_answer_accepts_int_for_slider():
    a = Answer(question_id="q1.1", value=42, language=Language.ARABIC)
    assert a.value == 42
    assert a.language == Language.ARABIC


def test_answer_accepts_list_for_multi_choice():
    a = Answer(question_id="q1.5", value=["hospitality", "faith"], language=Language.ENGLISH)
    assert a.value == ["hospitality", "faith"]


def test_answer_accepts_str_for_free_text():
    a = Answer(
        question_id="q5.4",
        value="We exist to make travel feel personal.",
        language=Language.ENGLISH,
    )
    assert isinstance(a.value, str)


def test_questionnaire_instance_starts_with_no_completion_time():
    qi = QuestionnaireInstance(
        session_id=uuid.uuid4(),
        questionnaire_version_id=uuid.uuid4(),
    )
    assert qi.completed_at is None
    assert qi.answers == []


def test_question_constraint_fields_default_to_none():
    q = _slider_question()
    assert q.min_selections is None
    assert q.max_selections is None
    assert q.free_text_max_length is None


def test_multi_choice_question_carries_selection_constraints():
    q = Question(
        id="q3.4",
        section="tensions",
        text_by_language={
            Language.ENGLISH: "Pick top frustrations",
            Language.ARABIC: "اختر أبرز الإحباطات",
        },
        mechanic=AnswerMechanic.MULTI_CHOICE,
        options=[
            AnswerOption(
                value="obscurity",
                label_by_language={
                    Language.ENGLISH: "People don't know us",
                    Language.ARABIC: "لا يعرفنا الناس",
                },
            ),
        ],
        min_selections=1,
        max_selections=3,
    )
    assert q.min_selections == 1
    assert q.max_selections == 3
    assert q.free_text_max_length is None


def test_free_text_question_carries_length_cap():
    q = Question(
        id="q5.4",
        section="aspiration",
        text_by_language={
            Language.ENGLISH: "Why does your brand exist?",
            Language.ARABIC: "لماذا توجد علامتك؟",
        },
        mechanic=AnswerMechanic.FREE_TEXT,
        free_text_max_length=500,
        required=False,
    )
    assert q.free_text_max_length == 500
    assert q.min_selections is None
    assert q.max_selections is None
