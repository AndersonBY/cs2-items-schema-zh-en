"""File management service for JSON and SQL files."""

import json
from pathlib import Path
from typing import Any

from ..config import Settings
from ..exceptions import ConfigurationError


class FileManager:
    """Service for managing file I/O operations."""

    def __init__(self, settings: Settings):
        self.settings = settings

    def load_required_schemas(self) -> dict[str, Any]:
        """Load required schema files from disk."""
        schemas = {}

        for filename in self.settings.REQUIRED_SCHEMA_FILES:
            file_path = self.settings.resource_dir / filename
            if not file_path.exists():
                raise ConfigurationError(
                    f"Required schema file not found: {filename}", details={"path": str(file_path)}
                )

            try:
                with file_path.open("r", encoding="utf-8") as f:
                    key = filename.replace(".json", "").replace("_", "")
                    schemas[key] = json.load(f)
            except (OSError, json.JSONDecodeError) as e:
                raise ConfigurationError(
                    f"Failed to load schema file {filename}: {e}", details={"path": str(file_path)}
                ) from e

        return schemas

    def save_json_files(self, *files: tuple[str | Path, dict | list]) -> None:
        """Save multiple JSON files to the resource directory."""
        self.settings.resource_dir.mkdir(parents=True, exist_ok=True)

        for filename, data in files:
            file_path = self.settings.resource_dir / filename
            try:
                with file_path.open("w", encoding="utf-8") as f:
                    json.dump(
                        data,
                        f,
                        sort_keys=self.settings.sort_keys,
                        indent=self.settings.json_indent,
                        ensure_ascii=self.settings.ensure_ascii,
                    )
            except (OSError, TypeError) as e:
                raise ConfigurationError(
                    f"Failed to save JSON file {filename}: {e}", details={"path": str(file_path)}
                ) from e

    def save_text_files(self, *files: tuple[str | Path, str]) -> None:
        """Save multiple text files to the SQL directory."""
        self.settings.sql_dir.mkdir(parents=True, exist_ok=True)

        for filename, content in files:
            file_path = self.settings.sql_dir / filename
            try:
                with file_path.open("w", encoding="utf-8") as f:
                    f.write(content)
            except OSError as e:
                raise ConfigurationError(
                    f"Failed to save text file {filename}: {e}", details={"path": str(file_path)}
                ) from e
