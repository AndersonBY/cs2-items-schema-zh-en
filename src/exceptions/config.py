"""Configuration-related exception classes."""

from .base import CS2SchemaError


class ConfigurationError(CS2SchemaError):
    """Raised when configuration is invalid or missing."""

    pass
