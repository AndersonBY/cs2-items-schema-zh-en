"""Application settings and configuration."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import ClassVar

from .urls import DataUrls


@dataclass(frozen=True)
class Settings:
    """Application settings configuration."""

    # Directory paths
    resource_dir: Path = field(default_factory=lambda: Path("schemas"))
    sql_dir: Path = field(default_factory=lambda: Path("sql"))

    # Data URLs
    urls: DataUrls = field(default_factory=DataUrls)

    # HTTP settings
    request_timeout: int = 30
    max_concurrent_requests: int = 4

    # File settings
    json_indent: int = 2
    ensure_ascii: bool = False
    sort_keys: bool = True

    # Required schema files
    REQUIRED_SCHEMA_FILES: ClassVar[list[str]] = ["_phases_mapping.json", "phases.json", "origins.json", "wears.json"]

    def __post_init__(self):
        """Validate settings after initialization."""
        if not self.resource_dir.exists():
            self.resource_dir.mkdir(parents=True, exist_ok=True)
        if not self.sql_dir.exists():
            self.sql_dir.mkdir(parents=True, exist_ok=True)
