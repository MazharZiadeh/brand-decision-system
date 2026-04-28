from src.llm.models import ModelVersion


def test_mock_fixed_member_present():
    assert ModelVersion.MOCK_FIXED.value == "mock-fixed-v1"


def test_mock_variable_member_present():
    assert ModelVersion.MOCK_VARIABLE.value == "mock-variable-v1"


def test_only_mock_versions_are_pinned_yet():
    """Real provider versions land when the bake-off completes; until then
    only the two mock identifiers exist. This test fails loudly if a real
    identifier was added without updating the docstring or audit trail."""
    assert {v.value for v in ModelVersion} == {"mock-fixed-v1", "mock-variable-v1"}
