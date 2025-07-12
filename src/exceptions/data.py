"""Data-related exception classes."""

from .base import CS2SchemaError


class DataFetchError(CS2SchemaError):
    """Raised when data fetching fails."""

    pass


class DataValidationError(CS2SchemaError):
    """Raised when data validation fails."""

    pass
