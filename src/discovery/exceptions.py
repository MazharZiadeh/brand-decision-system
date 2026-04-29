"""Discovery-Service-specific exceptions.

`ContentLoadError` is raised by the YAML loader on any failure (missing
file, malformed YAML, Pydantic validation error). Per CLAUDE.md §5
content-validation failures are loud — the app refuses to start rather
than silently degrade.

`DiscoveryError` is the broader Discovery-layer base for runtime
failures the Discovery Service produces (e.g., narrative generation
called with no tagged pain categories).
"""


class DiscoveryError(Exception):
    """Base class for Discovery-Service failures."""


class ContentLoadError(DiscoveryError):
    """A content YAML file is missing, malformed, or fails domain validation."""
