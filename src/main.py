import asyncio
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional, Union

import aiohttp
from multidict import CIMultiDict
import vdf  # type: ignore

from . import typings

from .fields import FieldsCollector
from .items import ItemsCollector
from .sticker_kits import StickerKitsCollector
from .containers import ContainersCollector
from .sql import SQLCreator


@dataclass(eq=False, repr=False)
class ResourceCollector:
    resource_dir: Path = field(default_factory=lambda: Path("schemas"))
    sql_dir: Path = field(default_factory=lambda: Path("sql"))

    items_game_url: str = "https://raw.githubusercontent.com/AndersonBY/cs-files-zh-en/master/static/items_game.txt"
    csgo_english_url: str = "https://raw.githubusercontent.com/AndersonBY/cs-files-zh-en/master/static/csgo_english.txt"
    csgo_schinese_url: str = "https://raw.githubusercontent.com/AndersonBY/cs-files-zh-en/master/static/csgo_schinese.txt"
    items_game_cdn_url: str = "https://raw.githubusercontent.com/AndersonBY/cs-files-zh-en/master/static/items_game_cdn.txt"

    # predefined schemas
    phases: Optional[dict[str, str]] = None
    origins: Optional[dict[str, str]] = None
    wears: Optional[list[dict[str, Any]]] = None

    _phases_mapping: Optional[dict[str, str]] = None

    def __post_init__(self):
        with (self.resource_dir / "_phases_mapping.json").open("r") as p:
            self._phases_mapping = json.load(p)

        with (self.resource_dir / "phases.json").open("r") as p:
            self.phases = json.load(p)

        with (self.resource_dir / "origins.json").open("r") as p:
            self.origins = json.load(p)

        with (self.resource_dir / "wears.json").open("r") as p:
            self.wears = json.load(p)

    async def fetch_data(self) -> tuple[typings.ITEMS_GAME, typings.CSGO_ENGLISH, typings.CSGO_SCHINESE, typings.ITEMS_CDN]:
        async with aiohttp.ClientSession() as session:
            tasks = (
                session.get(self.items_game_url),
                session.get(self.csgo_english_url),
                session.get(self.csgo_schinese_url),
                session.get(self.items_game_cdn_url),
            )

            resps = await asyncio.gather(*tasks)
            items_game_raw, csgo_english_raw, csgo_schinese_raw, items_game_cdn_raw = [await resp.text() for resp in resps]

        items_game = vdf.loads(items_game_raw)["items_game"]
        csgo_english: typings.CSGO_ENGLISH = CIMultiDict(vdf.loads(csgo_english_raw)["lang"]["Tokens"])
        csgo_schinese: typings.CSGO_SCHINESE = CIMultiDict(vdf.loads(csgo_schinese_raw)["lang"]["Tokens"])
        items_cdn = {k: v for k, v in (line.split("=") for line in items_game_cdn_raw.splitlines()[3:])}

        return items_game, csgo_english, csgo_schinese, items_cdn

    @staticmethod
    def dump_json_files(*files: tuple[Union[str, Path], Union[dict, list]], dir: Path):
        for file_name, file in files:
            with (dir / file_name).open("w") as f:
                json.dump(file, f, sort_keys=True, indent=2, ensure_ascii=False)

    @staticmethod
    def dump_files(*files: tuple[Union[str, Path], str], dir: Path):
        for file_name, file in files:
            with (dir / file_name).open("w", encoding="utf8") as f:
                f.write(file)

    async def collect(self):
        items_game, csgo_english, csgo_schinese, items_cdn = await self.fetch_data()

        if self._phases_mapping is None:
            raise ValueError("Phases mapping not loaded")
        fields_collector = FieldsCollector(items_game, csgo_english, csgo_schinese, self._phases_mapping)
        types, qualities, definitions, paints, rarities, musics, tints = fields_collector()

        containers_collector = ContainersCollector(items_game, csgo_english, csgo_schinese)
        weapon_cases, souvenir_cases, sticker_capsules, patch_capsules, music_kits = containers_collector()
        containers = {**weapon_cases, **souvenir_cases}
        sticker_kit_containers = {**sticker_capsules, **patch_capsules}

        items_collector = ItemsCollector(
            items_game,
            csgo_english,
            items_cdn,
            paints,
            definitions,
            containers,
        )
        items = items_collector()

        sticker_kit_collector = StickerKitsCollector(items_game, csgo_english, csgo_schinese, sticker_kit_containers)
        stickers, patches, graffities = sticker_kit_collector()
        sticker_kits = {**stickers, **patches, **graffities}

        to_json_dump = [
            ("types.json", types),
            ("qualities.json", qualities),
            ("definitions.json", definitions),
            ("paints.json", paints),
            ("musics.json", musics),
            ("rarities.json", rarities),
            ("containers.json", containers),
            ("sticker_kit_containers.json", sticker_kit_containers),
            ("items.json", items),
            ("sticker_kits.json", sticker_kits),
            ("music_kits.json", music_kits),
            ("tints.json", tints),
        ]

        if self.phases is None or self.wears is None or self.origins is None:
            raise ValueError("Required data not loaded")
        sql_creator = SQLCreator(**{k.split(".json")[0]: v for k, v in to_json_dump}, phases=self.phases, wears=self.wears, origins=self.origins)
        sql_dumps = sql_creator.create()

        self.dump_json_files(*to_json_dump, dir=self.resource_dir)
        self.dump_files(*sql_dumps, dir=self.sql_dir)
