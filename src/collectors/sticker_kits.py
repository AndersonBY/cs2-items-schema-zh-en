"""Sticker kits collector for CS2 game data."""

from typing import Any

from ..models.types import GameData
from .base import BaseCollector


class StickerKitsCollector(BaseCollector):
    """Collector for sticker kit data."""

    def __init__(self, game_data: GameData, sticker_kit_containers: dict[str, dict[str, Any]]) -> None:
        super().__init__(game_data)
        self.sticker_kit_containers = sticker_kit_containers

    def collect(self) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
        """
        Collect sticker kit data from items_game.

        Returns:
            Tuple of (stickers, patches, graffities) dictionaries
        """
        stickers = {}
        patches = {}
        graffities = {}

        sticker_kits_data = self.game_data.items_game.get("sticker_kits", {})

        for sticker_kit_index, sticker_kit_data in sticker_kits_data.items():
            try:
                # Get English name
                if "item_name" not in sticker_kit_data:
                    continue

                item_name_key = sticker_kit_data["item_name"]
                # Remove leading '#' if present
                if item_name_key.startswith("#"):
                    item_name_key = item_name_key[1:]

                english_name = self.game_data.csgo_english.get(item_name_key, "")
                chinese_name = self.game_data.csgo_schinese.get(item_name_key, english_name)

                if not english_name:
                    continue

                sticker_kit = {
                    "name": english_name,
                    "name_english": english_name,
                    "name_chinese": chinese_name,
                }

            except (KeyError, AttributeError):
                continue

            # Find containers that contain this sticker kit
            if containers := self._find_containers_with_sticker(sticker_kit_index):
                sticker_kit["containers"] = containers

            # Get rarity if available
            if rarity_key := sticker_kit_data.get("item_rarity"):
                rarities = self.game_data.items_game.get("rarities", {})
                if rarity_key in rarities:
                    sticker_kit["rarity"] = rarities[rarity_key].get("value", "")

            # Get sticker image path if available
            if "sticker_material" in sticker_kit_data:
                sticker_kit["image"] = sticker_kit_data["sticker_material"]

            # Get description if available
            if "description_string" in sticker_kit_data:
                desc_key = sticker_kit_data["description_string"]
                if desc_key.startswith("#"):
                    desc_key = desc_key[1:]
                desc_english = self.game_data.csgo_english.get(desc_key, "")
                desc_chinese = self.game_data.csgo_schinese.get(desc_key, desc_english)
                if desc_english:
                    sticker_kit["description_english"] = desc_english
                    sticker_kit["description_chinese"] = desc_chinese

            # Categorize by type based on name
            sticker_name = sticker_kit_data.get("name", "").lower()
            if "patch" in sticker_name:
                patches[sticker_kit_index] = sticker_kit
            elif "graffiti" in sticker_name:
                graffities[sticker_kit_index] = sticker_kit
            else:
                stickers[sticker_kit_index] = sticker_kit

        return stickers, patches, graffities

    def _find_containers_with_sticker(self, sticker_kit_index: str) -> list[str]:
        """Find containers that contain this sticker kit."""
        containers = set()

        for cont_index, cont_data in self.sticker_kit_containers.items():
            if "kits" in cont_data and sticker_kit_index in cont_data["kits"]:
                containers.add(cont_index)

        return sorted(containers)
