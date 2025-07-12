"""Containers collector for CS2 game data."""

import re
from typing import Any, cast

from .base import BaseCollector


class ContainersCollector(BaseCollector):
    """Collector for container data including weapon cases, sticker capsules, and music kits."""

    ITEM_NAME_RE = re.compile(r"\[(.+)](.+)")

    def collect(self) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
        """
        Collect container data from items_game.

        Returns:
            Tuple of (weapon_cases, souvenir_cases, sticker_capsules, patch_capsules, music_kits)
        """
        weapon_cases: dict[str, Any] = {}
        souvenir_cases: dict[str, Any] = {}
        sticker_capsules: dict[str, Any] = {}
        patch_capsules: dict[str, Any] = {}
        music_kits: dict[str, Any] = {}

        items = self.game_data.items_game.get("items", {})

        for defindex, item_data in items.items():
            if not self._check_case_prefab(item_data):
                continue

            container = {}

            # Handle item set containers (weapon cases and souvenir packages)
            if item_set_tag := item_data.get("tags", {}).get("ItemSet"):
                container = self._process_item_set_container(item_data, item_set_tag)
                if item_data.get("prefab") == "weapon_case_souvenirpkg":
                    containers_to_add = souvenir_cases
                else:
                    containers_to_add = weapon_cases

            # Handle sticker capsules
            elif sticker_caps_tag := item_data.get("tags", {}).get("StickerCapsule"):
                container = self._process_sticker_capsule(item_data, sticker_caps_tag)
                containers_to_add = sticker_capsules

            # Handle patch capsules
            elif patch_caps_tag := item_data.get("tags", {}).get("PatchCapsule"):
                container = self._process_patch_capsule(item_data, patch_caps_tag)
                containers_to_add = patch_capsules

            # Handle revolving loot list containers
            elif self._has_revolving_loot_list(item_data):
                container = self._process_revolving_loot_container(item_data)
                if "musickit" in item_data["name"]:
                    containers_to_add = music_kits
                else:
                    containers_to_add = sticker_capsules

            # Handle direct loot list containers
            elif "loot_list_name" in item_data:
                container = self._process_direct_loot_container(item_data)
                if "musickit" in item_data["name"] or "music_kits" in item_data.get("image_inventory", ""):
                    containers_to_add = music_kits
                elif "coupon" in item_data["name"]:
                    containers_to_add = sticker_capsules
                else:
                    containers_to_add = sticker_capsules

            else:
                continue  # Skip containers without loot lists

            # Add container if it has valid content
            if container and (container.get("items") or container.get("kits") or container.get("musics")):
                containers_to_add[defindex] = container

        return weapon_cases, souvenir_cases, sticker_capsules, patch_capsules, music_kits

    def _check_case_prefab(self, data: dict[str, Any]) -> bool:
        """Check if item has weapon_case_base prefab by walking the prefab hierarchy."""
        if "prefab" in data:
            if data["prefab"] == "weapon_case_base":
                return True
            else:
                prefabs = self.game_data.items_game.get("prefabs", {})
                return self._check_case_prefab(prefabs.get(data["prefab"], {}))
        return False

    def _process_item_set_container(self, item_data: dict[str, Any], item_set_tag: dict[str, Any]) -> dict[str, Any]:
        """Process containers that use item sets."""
        container = {}
        item_sets = self.game_data.items_game.get("item_sets", {})

        if item_set_tag["tag_value"] in item_sets:
            item_set = item_sets[item_set_tag["tag_value"]]
            loot_list = list(item_set.get("items", {}).keys())
            container["items"] = [self._find_item_indexes(item) for item in loot_list if self._find_item_indexes(item)]

        if "associated_items" in item_data:
            container["associated"] = list(item_data["associated_items"].keys())[0]

        return container

    def _process_sticker_capsule(self, item_data: dict[str, Any], sticker_caps_tag: dict[str, Any]) -> dict[str, Any]:
        """Process sticker capsules."""
        loot_dict = self._get_loot_dict_for_sticker_capsule(item_data, sticker_caps_tag)
        if not loot_dict:
            return {}

        loot_list = self._get_loot_recursive(loot_dict)
        kits = [self._find_sticker_kit_index(item) for item in loot_list if self._find_sticker_kit_index(item)]

        return {"kits": kits} if kits else {}

    def _process_patch_capsule(self, item_data: dict[str, Any], patch_caps_tag: dict[str, Any]) -> dict[str, Any]:
        """Process patch capsules."""
        client_loot_lists = self.game_data.items_game.get("client_loot_lists", {})
        loot_dict = None

        if patch_caps_tag["tag_value"] in client_loot_lists:
            loot_dict = client_loot_lists[patch_caps_tag["tag_value"]]
        elif item_data["name"] in client_loot_lists:
            loot_dict = client_loot_lists[item_data["name"]]

        if not loot_dict:
            return {}

        loot_list = self._get_loot_recursive(loot_dict)
        kits = [self._find_sticker_kit_index(item) for item in loot_list if self._find_sticker_kit_index(item)]

        return {"kits": kits} if kits else {}

    def _has_revolving_loot_list(self, item_data: dict[str, Any]) -> bool:
        """Check if item has revolving loot list."""
        series_value = item_data.get("attributes", {}).get("set supply crate series", {}).get("value")
        if not series_value:
            return False

        revolving_loot_lists = self.game_data.items_game.get("revolving_loot_lists", {})
        client_loot_lists = self.game_data.items_game.get("client_loot_lists", {})

        return series_value in revolving_loot_lists and revolving_loot_lists[series_value] in client_loot_lists

    def _process_revolving_loot_container(self, item_data: dict[str, Any]) -> dict[str, Any]:
        """Process containers with revolving loot lists."""
        series_value = item_data["attributes"]["set supply crate series"]["value"]
        revolving_loot_lists = self.game_data.items_game.get("revolving_loot_lists", {})
        client_loot_lists = self.game_data.items_game.get("client_loot_lists", {})

        loot_dict = client_loot_lists[revolving_loot_lists[series_value]]
        loot_list = self._get_loot_recursive(loot_dict)

        if "musickit" in item_data["name"]:
            musics = [self._find_music_kit_index(item) for item in loot_list if self._find_music_kit_index(item)]
            return {"musics": musics} if musics else {}
        else:
            kits = [self._find_sticker_kit_index(item) for item in loot_list if self._find_sticker_kit_index(item)]
            return {"kits": kits} if kits else {}

    def _process_direct_loot_container(self, item_data: dict[str, Any]) -> dict[str, Any]:
        """Process containers with direct loot list names."""
        client_loot_lists = self.game_data.items_game.get("client_loot_lists", {})

        if item_data["loot_list_name"] not in client_loot_lists:
            return {}

        loot_dict = client_loot_lists[item_data["loot_list_name"]]
        loot_list = self._get_loot_recursive(loot_dict)

        if "musickit" in item_data["name"] or "music_kits" in item_data.get("image_inventory", ""):
            musics = [self._find_music_kit_index(item) for item in loot_list if self._find_music_kit_index(item)]
            return {"musics": musics} if musics else {}
        else:
            kits = [self._find_sticker_kit_index(item) for item in loot_list if self._find_sticker_kit_index(item)]
            return {"kits": kits} if kits else {}

    def _get_loot_dict_for_sticker_capsule(
        self, item_data: dict[str, Any], sticker_caps_tag: dict[str, Any]
    ) -> dict[str, Any] | None:
        """Get loot dictionary for sticker capsule."""
        client_loot_lists = self.game_data.items_game.get("client_loot_lists", {})
        revolving_loot_lists = self.game_data.items_game.get("revolving_loot_lists", {})

        # Try tag value first
        if sticker_caps_tag["tag_value"] in client_loot_lists:
            return cast(dict[str, Any], client_loot_lists[sticker_caps_tag["tag_value"]])

        # Try item name
        if item_data["name"] in client_loot_lists:
            return cast(dict[str, Any], client_loot_lists[item_data["name"]])

        # Try revolving loot list
        series_value = item_data.get("attributes", {}).get("set supply crate series", {}).get("value")
        if (
            series_value
            and series_value in revolving_loot_lists
            and revolving_loot_lists[series_value] in client_loot_lists
        ):
            return cast(dict[str, Any], client_loot_lists[revolving_loot_lists[series_value]])

        return None

    def _get_loot_recursive(self, entry: dict[str, Any]) -> list[str]:
        """Recursively get loot items from nested loot lists."""
        loot = []
        client_loot_lists = self.game_data.items_game.get("client_loot_lists", {})

        for loot_name in entry.keys():
            if "[" in loot_name:
                loot.append(loot_name)
            else:
                loot.extend(self._get_loot_recursive(client_loot_lists.get(loot_name, {})))

        return loot

    def _find_item_indexes(self, item_name: str) -> str | None:
        """Find item indexes for paint and definition combination."""
        try:
            matches = self.ITEM_NAME_RE.findall(item_name)
            if not matches:
                return None

            paint_name, def_name = matches[0]
            items = self.game_data.items_game.get("items", {})
            paint_kits = self.game_data.items_game.get("paint_kits", {})

            # Find definition index
            def_index = None
            for defindex, type_data in items.items():
                if type_data.get("name") == def_name:
                    def_index = defindex
                    break

            if not def_index:
                return None

            # Find paint index
            paint_index = None
            for paint_idx, paint_data in paint_kits.items():
                if paint_data.get("name") == paint_name:
                    paint_index = paint_idx
                    break

            if not paint_index:
                return None

            return f"[{paint_index}]{def_index}"
        except (IndexError, KeyError):
            return None

    def _find_sticker_kit_index(self, item_name: str) -> str | None:
        """Find sticker kit index from item name."""
        try:
            matches = self.ITEM_NAME_RE.findall(item_name)
            if not matches:
                return None

            sticker_kit_name, def_name = matches[0]
            sticker_kits = self.game_data.items_game.get("sticker_kits", {})

            for sticker_id, sticker_kit_data in sticker_kits.items():
                if sticker_kit_data.get("name") == sticker_kit_name:
                    return sticker_id
        except (IndexError, KeyError):
            pass
        return None

    def _find_music_kit_index(self, item_name: str) -> str | None:
        """Find music kit index from item name."""
        try:
            matches = self.ITEM_NAME_RE.findall(item_name)
            if not matches:
                return None

            music_kit_name, def_name = matches[0]
            music_definitions = self.game_data.items_game.get("music_definitions", {})

            for music_id, music_kit_data in music_definitions.items():
                if music_kit_data.get("name") == music_kit_name:
                    return music_id
        except (IndexError, KeyError):
            pass
        return None
