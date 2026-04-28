class DomainError(Exception):
    """Base class for every exception raised inside the domain layer.

    Catch this at API and service boundaries to convert domain failures into
    user-facing 4xx responses without swallowing infrastructure errors.
    """


class InvalidScopeError(DomainError):
    """The DecisionScope is empty or contains modules outside ModuleId."""


class LanguageMismatchError(DomainError):
    """A model's language tag conflicts with a related model's language tag."""


class MissingUpstreamError(DomainError):
    """A downstream output references upstream IDs that do not exist."""


class RuleEvaluationError(DomainError):
    """The Rules Engine failed to evaluate a rule against the given answers."""
