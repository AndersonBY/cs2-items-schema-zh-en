"""Base exception classes."""


class CS2SchemaError(Exception):
    """Base exception for all CS2 schema related errors."""

    def __init__(self, message: str, details: dict | None = None):
        super().__init__(message)
        self.details = details or {}
