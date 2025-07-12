from dataclasses import dataclass
from typing import Any

from . import typings


@dataclass(eq=False, repr=False)
class StickerKitsCollector:
    """Collect stickers, tints, patches, graffities"""

    items_game: typings.ITEMS_GAME
    csgo_english: typings.CSGO_ENGLISH
    csgo_schinese: typings.CSGO_SCHINESE

    containers: dict[str, dict[str, Any]]

    def _find_containers(self, sticker_kit_index: str) -> list[str]:
        containers = set()
        for cont_index, cont in self.containers.items():
            kits = cont.get("kits", [])
            if isinstance(kits, list) and sticker_kit_index in kits:
                containers.add(cont_index)

        return list(containers)

    def __call__(self) -> tuple[dict[str, dict[str, Any]], ...]:
        stickers = {}
        patches = {}
        graffities = {}

        sticker_kit_data: dict[str, str]
        for sticker_kit_index, sticker_kit_data in self.items_game["sticker_kits"].items():
            try:
                sticker_kit_name_key = sticker_kit_data["item_name"][1:]
                sticker_kit: dict[str, Any] = {
                    "name": self.csgo_english[sticker_kit_name_key],
                    "name_zh": self.csgo_schinese.get(sticker_kit_name_key, self.csgo_english[sticker_kit_name_key]),
                }

            except KeyError:
                continue

            found_containers = self._find_containers(sticker_kit_index)
            if found_containers:
                sticker_kit["containers"] = found_containers

            if rarity_key := sticker_kit_data.get("item_rarity"):
                sticker_kit["rarity"] = self.items_game["rarities"][rarity_key]["value"]

            # there can be image

            if "patch" in sticker_kit_data["name"]:
                patches[sticker_kit_index] = sticker_kit
            elif "graffiti" in sticker_kit_data["name"]:
                graffities[sticker_kit_index] = sticker_kit
            else:
                stickers[sticker_kit_index] = sticker_kit

        return stickers, patches, graffities
