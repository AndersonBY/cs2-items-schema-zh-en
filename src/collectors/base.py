"""Base collector class with common functionality."""

from abc import ABC, abstractmethod
from typing import Any

from ..exceptions import DataValidationError
from ..models.types import GameData


class BaseCollector(ABC):
    """Abstract base class for all data collectors."""

    def __init__(self, game_data: GameData):
        self.game_data = game_data
        self._validate_game_data()

    def _validate_game_data(self) -> None:
        """Validate that required game data is present."""
        if not self.game_data.items_game:
            raise DataValidationError("items_game data is missing or empty")
        if not self.game_data.csgo_english:
            raise DataValidationError("csgo_english data is missing or empty")
        if not self.game_data.csgo_schinese:
            raise DataValidationError("csgo_schinese data is missing or empty")

    def _get_localized_name(self, key: str, fallback: str = "") -> tuple[str, str]:
        """Get English and Chinese localized names for a key."""
        english_name = self.game_data.csgo_english.get(key, fallback)
        chinese_name = self.game_data.csgo_schinese.get(key, english_name)
        return english_name, chinese_name

    def _find_top_level_prefab(self, data: dict[str, Any], attr: str) -> dict[str, Any]:
        """Find the top-level prefab containing the specified attribute."""
        if data.get(attr):
            return data

        prefab_key = self._normalize_prefab_key(data.get("prefab", ""))
        if not prefab_key:
            raise KeyError(f"No prefab found for attribute: {attr}")

        prefabs = self.game_data.items_game.get("prefabs", {})
        if prefab_key not in prefabs:
            raise KeyError(f"Prefab not found: {prefab_key}")

        return self._find_top_level_prefab(prefabs[prefab_key], attr)

    def _normalize_prefab_key(self, prefab: str) -> str:
        """Normalize prefab key by handling special cases."""
        if not prefab:
            return ""

        if "valve" in prefab:
            parts = prefab.split(" ")
            return parts[1] if len(parts) > 1 else ""
        elif " " in prefab:
            return prefab.split(" ")[0]
        else:
            return prefab

    @abstractmethod
    def collect(self) -> Any:
        """Collect and process data. Must be implemented by subclasses."""
        pass
