from dataclasses import dataclass
from typing import Any, Union

from . import typings


@dataclass(eq=False, repr=False)
class ItemsCollector:
    items_game: typings.ITEMS_GAME
    csgo_english: typings.CSGO_ENGLISH
    items_cdn: typings.ITEMS_CDN

    paints: dict[str, dict[str, Any]]
    definitions: dict[str, dict[str, str]]
    containers: dict[str, dict[str, Union[str, list[str]]]]

    def _create_painted_item_name(self, defindex: str, paint_index: str) -> str:
        paint_codename = "_" + self.items_game["paint_kits"][paint_index]["name"]
        item_codename = self.items_game["items"][defindex]["name"]
        return item_codename + paint_codename

    def _find_containers(self, defindex: str, paintindex: str) -> list[str]:
        containers = set()
        for cont_index, cont in self.containers.items():
            items_value = cont.get("items")
            if isinstance(items_value, list) and "[" + paintindex + "]" + defindex in items_value:
                containers.add(cont_index)

        return list(containers)

    def _check_paintable(self, item_data: dict[str, Any]) -> bool:
        item_name = item_data.get("name", "")
        return bool(next((k for k in self.items_cdn.keys() if item_name in k), None))

    def __call__(self) -> dict[str, dict[str, Union[str, list[str]]]]:
        items: dict[str, dict[str, Union[str, list[str]]]] = {}

        for defindex, item_data in self.items_game["items"].items():
            if defindex not in self.definitions:  # skip non-tradable and trash
                continue

            if not self._check_paintable(item_data):  # non-paintable
                item: dict[str, Union[str, list[str]]] = {
                    "def": defindex,
                }

                items[defindex] = item

            else:
                # find possible combination defindex + paintindex = item with paint
                for paint_index, paint_data in self.paints.items():
                    item_name = self._create_painted_item_name(defindex, paint_index)
                    if item_name in self.items_cdn:
                        painted_item: dict[str, Union[str, list[str]]] = {
                            "def": defindex,
                            "image": self.items_cdn[item_name],
                            "paint": paint_index,
                        }

                        found_containers = self._find_containers(defindex, paint_index)
                        if found_containers:
                            painted_item["containers"] = found_containers

                        items[f"[{paint_index}]{defindex}"] = painted_item

        return items
