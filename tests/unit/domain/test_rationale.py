import uuid

import pytest
from pydantic import ValidationError

from src.domain.language import Language
from src.domain.rationale import PriorityFactor, Rationale


def test_priority_factor_is_frozen():
    pf = PriorityFactor(
        factor_name="Audience perception",
        how_addressed="Lands clearly with Saudi professionals.",
    )
    with pytest.raises(ValidationError):
        pf.factor_name = "Other"  # type: ignore[misc]


def test_rationale_requires_language():
    with pytest.raises(ValidationError):
        Rationale(  # type: ignore[call-arg]
            priority_factors_addressed=[],
            narrative="why this works",
        )


def test_valid_rationale():
    r = Rationale(
        priority_factors_addressed=[
            PriorityFactor(
                factor_name="Strategic positioning",
                how_addressed="Reinforces the challenger stance.",
            ),
        ],
        narrative="The strategy expresses the brand's challenger posture.",
        language=Language.ENGLISH,
        upstream_inputs_referenced=[uuid.uuid4()],
    )
    assert r.priority_factors_addressed[0].factor_name == "Strategic positioning"
    assert r.language == Language.ENGLISH
