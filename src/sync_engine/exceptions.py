class SyncError(Exception):
    """Base exception for all sync engine errors."""


class ConfigurationError(SyncError):
    """Raised when configuration is missing or invalid at startup."""


class MappingError(SyncError):
    """Raised when file mapping cannot be resolved."""


class AnalysisError(SyncError):
    """Raised when AST analysis fails (e.g. syntax error in source)."""


class ValidationError(SyncError):
    """Raised when updated documentation fails validation."""


class UpdateError(SyncError):
    """Raised when a documentation file cannot be written."""
