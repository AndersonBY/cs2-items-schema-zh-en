"""Type definitions and data models."""

from dataclasses import dataclass
from typing import Any, TypeAlias

from multidict import CIMultiDict

# Type aliases for game data
ItemsGame: TypeAlias = dict[str, dict[str, Any]]
CsgoEnglish: TypeAlias = CIMultiDict[str]
CsgoSchinese: TypeAlias = CIMultiDict[str]
ItemsCdn: TypeAlias = dict[str, str]
PhasesMapping: TypeAlias = dict[str, str]


@dataclass(frozen=True)
class GameData:
    """Container for raw game data from external sources."""

    items_game: ItemsGame
    csgo_english: CsgoEnglish
    csgo_schinese: CsgoSchinese
    items_cdn: ItemsCdn


@dataclass(frozen=True)
class ProcessedData:
    """Container for processed game data ready for export."""

    types: dict[str, str]
    qualities: dict[str, dict[str, str]]
    definitions: dict[str, dict[str, Any]]
    paints: dict[str, dict[str, Any]]
    rarities: dict[str, dict[str, Any]]
    musics: dict[str, dict[str, str]]
    tints: dict[str, dict[str, str]]
    containers: dict[str, dict[str, Any]]
    sticker_kit_containers: dict[str, dict[str, Any]]
    items: dict[str, dict[str, Any]]
    sticker_kits: dict[str, dict[str, Any]]
    music_kits: dict[str, dict[str, Any]]
