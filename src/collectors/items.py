"""Items collector for CS2 game data."""

from typing import Any

from .base import BaseCollector


class ItemsCollector(BaseCollector):
    """Collector for individual item data including painted and non-painted items."""

    def __init__(
        self,
        game_data,
        paints: dict[str, Any],
        definitions: dict[str, dict[str, Any]],
        containers: dict[str, dict[str, Any]],
    ):
        super().__init__(game_data)
        self.paints = paints
        self.definitions = definitions
        self.containers = containers

    def collect(self) -> dict[str, dict[str, Any]]:
        """
        Collect item data from items_game.

        Returns:
            Dictionary of items with their properties
        """
        items = {}
        items_game_items = self.game_data.items_game.get("items", {})

        for defindex, item_data in items_game_items.items():
            if defindex not in self.definitions:  # Skip non-tradable and trash
                continue

            if not self._check_paintable(item_data):  # Non-paintable items
                item = {
                    "def": defindex,
                }
                items[defindex] = item
            else:
                # Find possible combination defindex + paintindex = item with paint
                for paint_index in self.paints.keys():
                    item_name = self._create_painted_item_name(defindex, paint_index)
                    if item_name in self.game_data.items_cdn:
                        item = {
                            "def": defindex,
                            "image": self.game_data.items_cdn[item_name],
                            "paint": paint_index,
                        }

                        if containers := self._find_containers(defindex, paint_index):
                            item["containers"] = containers

                        items[f"[{paint_index}]{defindex}"] = item

        return items

    def _create_painted_item_name(self, defindex: str, paint_index: str) -> str:
        """Create painted item name by combining item and paint codenames."""
        paint_kits = self.game_data.items_game.get("paint_kits", {})
        items = self.game_data.items_game.get("items", {})

        if paint_index not in paint_kits or defindex not in items:
            return ""

        paint_codename = "_" + paint_kits[paint_index].get("name", "")
        item_codename = items[defindex].get("name", "")
        return item_codename + paint_codename

    def _find_containers(self, defindex: str, paintindex: str) -> list[str]:
        """Find containers that contain this specific item + paint combination."""
        containers = set()
        target_item = f"[{paintindex}]{defindex}"

        for cont_index, cont in self.containers.items():
            if "items" in cont and target_item in cont["items"]:
                containers.add(cont_index)

        return list(containers)

    def _check_paintable(self, item_data: dict[str, Any]) -> bool:
        """Check if item is paintable by looking for it in CDN data."""
        item_name = item_data.get("name", "")
        if not item_name:
            return False

        # Look for any CDN entry that contains this item name
        for cdn_key in self.game_data.items_cdn.keys():
            if item_name in cdn_key:
                return True
        return False
