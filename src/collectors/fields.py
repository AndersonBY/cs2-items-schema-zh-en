"""Fields collector for extracting basic game field data."""

from typing import Any

from ..exceptions import DataValidationError
from ..models.types import GameData, PhasesMapping
from .base import BaseCollector


class FieldsCollector(BaseCollector):
    """Collector for origins, qualities, types, paints and rarities from game data."""

    def __init__(self, game_data: GameData, phases_mapping: PhasesMapping):
        super().__init__(game_data)
        self.phases_mapping = phases_mapping
        self._types_mapping: dict[str, str] | None = None
        self._qualities_mapping: dict[str, str] = {}
        self._rarities_mapping: dict[str, str] = {}

    def collect(
        self,
    ) -> tuple[
        dict[str, str],  # types
        dict[str, dict[str, str]],  # qualities
        dict[str, dict[str, Any]],  # definitions
        dict[str, dict[str, Any]],  # paints
        dict[str, dict[str, Any]],  # rarities
        dict[str, dict[str, str]],  # musics
        dict[str, dict[str, str]],  # tints
    ]:
        """Collect all field data and return as tuple."""
        # Order matters - types must be processed first for definitions
        types = self._collect_types()
        self._types_mapping = self._invert_dict(types)

        qualities = self._collect_qualities()
        rarities = self._collect_rarities()
        definitions = self._collect_definitions()
        paints = self._collect_paints()
        musics = self._collect_music_definitions()
        tints = self._collect_tints()

        return types, qualities, definitions, paints, rarities, musics, tints

    def _collect_qualities(self) -> dict[str, dict[str, str]]:
        """Extract quality data."""
        qualities = {}
        qualities_data = self.game_data.items_game.get("qualities", {})

        for quality_key, quality_data in qualities_data.items():
            if not isinstance(quality_data, dict) or "value" not in quality_data:
                continue

            try:
                english_name, chinese_name = self._get_localized_name(quality_key)
                if english_name:  # Only include if we have a name
                    qualities[quality_data["value"]] = {
                        "name": english_name,
                        "name_zh": chinese_name,
                    }
                    self._qualities_mapping[quality_key] = quality_data["value"]
            except (KeyError, TypeError):
                continue

        return qualities

    def _collect_definitions(self) -> dict[str, dict[str, Any]]:
        """Extract item definition data."""
        definitions = {}
        items_data = self.game_data.items_game.get("items", {})

        if not self._types_mapping:
            raise DataValidationError("Types mapping not initialized")

        for defindex, item_data in items_data.items():
            if not isinstance(item_data, dict):
                continue

            try:
                item_name = self._find_item_name(item_data)
                definition = {
                    "name": item_name["en"],
                    "name_zh": item_name["zh"],
                    "type": self._find_item_type(item_data),
                }

                # Optional quality
                if quality_key := item_data.get("item_quality"):
                    if quality_key in self._qualities_mapping:
                        definition["quality"] = self._qualities_mapping[quality_key]

                # Optional rarity
                if rarity_key := item_data.get("item_rarity"):
                    if rarity_key in self._rarities_mapping:
                        definition["rarity"] = self._rarities_mapping[rarity_key]

                definitions[defindex] = definition

            except (KeyError, TypeError):
                continue

        return definitions

    def _collect_paints(self) -> dict[str, dict[str, Any]]:
        """Extract paint kit data."""
        paints = {}
        paint_kits = self.game_data.items_game.get("paint_kits", {})
        paint_kits_rarity = self.game_data.items_game.get("paint_kits_rarity", {})

        for paintindex, paint_data in paint_kits.items():
            if not isinstance(paint_data, dict) or paintindex == "0":
                continue

            try:
                description_tag = paint_data.get("description_tag", "")
                if not description_tag.startswith("#"):
                    continue

                tag_key = description_tag[1:]  # Remove # prefix
                english_name, chinese_name = self._get_localized_name(tag_key)

                paint = {
                    "name": english_name,
                    "name_zh": chinese_name,
                    "wear_min": float(paint_data.get("wear_remap_min", 0.06)),
                    "wear_max": float(paint_data.get("wear_remap_max", 0.8)),
                }

                # Check for Doppler phase
                if english_name and "doppler" in english_name.lower() and paintindex in self.phases_mapping:
                    paint["phase"] = self.phases_mapping[paintindex]

                # Optional rarity
                paint_name = paint_data.get("name", "")
                if paint_name and paint_name in paint_kits_rarity:
                    rarity_key = paint_kits_rarity[paint_name]
                    if rarity_key in self._rarities_mapping:
                        paint["rarity"] = self._rarities_mapping[rarity_key]

                paints[paintindex] = paint

            except (KeyError, ValueError, TypeError):
                continue

        return paints

    def _collect_rarities(self) -> dict[str, dict[str, Any]]:
        """Extract rarity data."""
        rarities = {}
        rarities_data = self.game_data.items_game.get("rarities", {})
        colors_data = self.game_data.items_game.get("colors", {})

        for rarity_key, rarity_data in rarities_data.items():
            if not isinstance(rarity_data, dict) or "value" not in rarity_data:
                continue

            try:
                # Required fields
                weapon_key = rarity_data.get("loc_key_weapon", "")
                nonweapon_key = rarity_data.get("loc_key", "")
                color_key = rarity_data.get("color", "")

                if not all([weapon_key, nonweapon_key, color_key]):
                    continue

                weapon_en, weapon_zh = self._get_localized_name(weapon_key)
                nonweapon_en, nonweapon_zh = self._get_localized_name(nonweapon_key)

                if not weapon_en or not nonweapon_en:
                    continue

                color_data = colors_data.get(color_key, {})
                hex_color = color_data.get("hex_color", "")
                if not hex_color:
                    continue

                rarity = {
                    "weapon": weapon_en,
                    "weapon_zh": weapon_zh,
                    "nonweapon": nonweapon_en,
                    "nonweapon_zh": nonweapon_zh,
                    "color": hex_color,
                }

                # Optional character rarity
                if character_key := rarity_data.get("loc_key_character"):
                    char_en, char_zh = self._get_localized_name(character_key)
                    if char_en:
                        rarity["character"] = char_en
                        rarity["character_zh"] = char_zh

                rarities[rarity_data["value"]] = rarity
                self._rarities_mapping[rarity_key] = rarity_data["value"]

            except (KeyError, TypeError):
                continue

        return rarities

    def _collect_types(self) -> dict[str, str]:
        """Extract item type data."""
        types = set()
        items_data = self.game_data.items_game.get("items", {})

        for item_data in items_data.values():
            if not isinstance(item_data, dict):
                continue

            try:
                top_prefab = self._find_top_level_prefab(item_data, "item_type_name")
                type_key = top_prefab.get("item_type_name", "")
                if type_key.startswith("#"):
                    type_name = self.game_data.csgo_english.get(type_key[1:])
                    if type_name:
                        types.add(type_name)
            except (KeyError, TypeError):
                continue

        return {str(i): t for i, t in enumerate(sorted(types))}

    def _collect_tints(self) -> dict[str, dict[str, str]]:
        """Extract graffiti tint data."""
        tints = {}
        tints_data = self.game_data.items_game.get("graffiti_tints", {})

        for tint_data in tints_data.values():
            if not isinstance(tint_data, dict) or "id" not in tint_data:
                continue

            tint_id = tint_data["id"]
            tint_key = f"Attrib_SprayTintValue_{tint_id}"

            english_name, chinese_name = self._get_localized_name(tint_key)
            if english_name:
                tints[tint_id] = {
                    "name": english_name,
                    "name_zh": chinese_name,
                }

        return tints

    def _collect_music_definitions(self) -> dict[str, dict[str, str]]:
        """Extract music kit definition data."""
        music_defs = {}
        music_data = self.game_data.items_game.get("music_definitions", {})

        for music_index, music_kit_data in music_data.items():
            if not isinstance(music_kit_data, dict):
                continue

            try:
                loc_name = music_kit_data.get("loc_name", "")
                if not loc_name.startswith("#"):
                    continue

                music_key = loc_name[1:]  # Remove # prefix
                english_name, chinese_name = self._get_localized_name(music_key)

                if english_name:
                    music_defs[music_index] = {
                        "name": english_name,
                        "name_zh": chinese_name,
                    }

            except (KeyError, TypeError):
                continue

        return music_defs

    def _find_item_name(self, item_data: dict[str, Any]) -> dict[str, str]:
        """Find the display name for an item."""
        prefab = self._find_top_level_prefab(item_data, "item_name")
        item_name_key = prefab.get("item_name", "")
        if item_name_key.startswith("#"):
            return {
                "en": self.game_data.csgo_english.get(item_name_key[1:], ""),
                "zh": self.game_data.csgo_schinese.get(item_name_key[1:], ""),
            }
        return {"en": "", "zh": ""}

    def _find_item_type(self, item_data: dict[str, Any]) -> str:
        """Find the type ID for an item."""
        if not self._types_mapping:
            raise DataValidationError("Types mapping not initialized")

        prefab = self._find_top_level_prefab(item_data, "item_type_name")
        type_name_key = prefab.get("item_type_name", "")

        if type_name_key.startswith("#"):
            type_name = self.game_data.csgo_english.get(type_name_key[1:])
            if type_name and type_name in self._types_mapping:
                return self._types_mapping[type_name]

        raise KeyError(f"Type not found for item: {item_data}")

    @staticmethod
    def _invert_dict(mapping: dict[str, Any]) -> dict[str, str]:
        """Invert a dictionary mapping."""
        return {v: k for k, v in mapping.items()}
