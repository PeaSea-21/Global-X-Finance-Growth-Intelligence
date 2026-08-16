class ValidationError(ValueError):
    """Raised when trusted configuration or evidence input is invalid."""


class DuplicateEvidenceError(ValidationError):
    """Raised when evidence conflicts with an existing exact duplicate."""

