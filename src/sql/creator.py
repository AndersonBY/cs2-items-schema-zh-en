from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy import Column, ForeignKey, Index, MetaData, Table, UniqueConstraint, create_mock_engine
from sqlalchemy.dialects import mssql, mysql, oracle, postgresql, sqlite
from sqlalchemy.engine.interfaces import Dialect
from sqlalchemy.types import Float, SmallInteger, String, TypeEngine

metadata = MetaData()

Types = Table(
    "types",
    metadata,
    Column("id", SmallInteger, primary_key=True, autoincrement=False),
    Column("name", String(16)),
)

Origins = Table(
    "origins",
    metadata,
    Column("id", SmallInteger, primary_key=True, autoincrement=False),
    Column("name", String(30)),
)

Qualities = Table(
    "qualities",
    metadata,
    Column("id", SmallInteger, primary_key=True, autoincrement=False),
    Column("name", String(16)),
    Column("name_zh", String(32)),
)

Phases = Table(
    "phases",
    metadata,
    Column("id", SmallInteger, primary_key=True, autoincrement=False),
    Column("name", String(16)),
)

Tints = Table(
    "tints",
    metadata,
    Column("id", SmallInteger, primary_key=True, autoincrement=False),
    Column("name", String(16)),
    Column("name_zh", String(32)),
)

Musics = Table(
    "musics",
    metadata,
    Column("id", SmallInteger, primary_key=True, autoincrement=False),
    Column("name", String(16)),
    Column("name_zh", String(32)),
)

Rarities = Table(
    "rarities",
    metadata,
    Column("id", SmallInteger, primary_key=True, autoincrement=False),
    Column("character", String(16)),
    Column("character_zh", String(32)),
    Column("color", String(16), nullable=False),
    Column("nonweapon", String(16), nullable=False),
    Column("nonweapon_zh", String(32)),
    Column("weapon", String(16), nullable=False),
    Column("weapon_zh", String(32)),
)

Wears = Table(
    "wears",
    metadata,
    Column("name", String(30), primary_key=True),
    Column("from", Float, nullable=False),
    Column("to", Float, nullable=False),
)

Definitions = Table(
    "definitions",
    metadata,
    Column("defindex", SmallInteger, primary_key=True, autoincrement=False),
    Column("name", String(60), nullable=False),
    Column("type", SmallInteger, ForeignKey(Types.c.id), nullable=False),
    Column("quality", SmallInteger, ForeignKey(Qualities.c.id)),
    Column("rarity", SmallInteger, ForeignKey(Rarities.c.id)),
)

Paints = Table(
    "paints",
    metadata,
    Column("paintindex", SmallInteger, primary_key=True, autoincrement=False),
    Column("name", String(60), nullable=False),
    Column("name_zh", String(120)),
    Column("wear_min", Float, nullable=False),
    Column("wear_max", Float, nullable=False),
    Column("rarity", SmallInteger, ForeignKey(Rarities.c.id), nullable=False),
    Column("phase", SmallInteger, ForeignKey(Phases.c.id)),
)

Items = Table(
    "items",
    metadata,
    Column("id", String(16), primary_key=True),
    Column("def", SmallInteger, ForeignKey(Definitions.c.defindex), nullable=False),
    Column("paint", SmallInteger, ForeignKey(Paints.c.paintindex)),
    Column("image", String(255)),
    UniqueConstraint("def", "paint", name="uniq_paint_def"),
    Index("ix_paint_def", "def", "paint", unique=True),
)

StickerKits = Table(
    "sticker_kits",
    metadata,
    Column("id", SmallInteger, primary_key=True, autoincrement=False),
    Column("name", String(60), nullable=False),
    Column("name_zh", String(120)),
    Column("rarity", SmallInteger, ForeignKey(Rarities.c.id)),
)

Containers = Table(
    "containers",
    metadata,
    Column("defindex", SmallInteger, ForeignKey(Items.c.id), primary_key=True),
    Column("associated", SmallInteger, ForeignKey(Items.c.id)),
    Column("set", String(60)),
)

StickerKitContainers = Table(
    "sticker_kit_containers",
    metadata,
    Column("defindex", SmallInteger, ForeignKey(Items.c.id), primary_key=True),
)

MusicKits = Table(
    "music_kits",
    metadata,
    Column("defindex", SmallInteger, ForeignKey(Items.c.id), primary_key=True),
)

ItemsContainersJunction = Table(
    "items_containers",
    metadata,
    Column("item", String(16), ForeignKey(Items.c.id), primary_key=True, nullable=False),
    Column("container", SmallInteger, ForeignKey(Containers.c.defindex), primary_key=True, nullable=False),
    UniqueConstraint("item", "container", name="uniq_item_container"),
    Index("idx_item_container", "item", "container", unique=True),
)

MusicsMusicKitsJunction = Table(
    "musics_music_kits",
    metadata,
    Column("music", SmallInteger, ForeignKey(Musics.c.id), primary_key=True, nullable=False),
    Column("container", SmallInteger, ForeignKey(MusicKits.c.defindex), primary_key=True, nullable=False),
    UniqueConstraint("music", "container", name="uniq_music_container"),
    Index("idx_music_container", "music", "container", unique=True),
)

StickerKitsContainersJunction = Table(
    "sticker_kits_containers",
    metadata,
    Column("kit", SmallInteger, ForeignKey(StickerKits.c.id), primary_key=True, nullable=False),
    Column("container", SmallInteger, ForeignKey(StickerKitContainers.c.defindex), primary_key=True, nullable=False),
    UniqueConstraint("kit", "container", name="uniq_kit_container"),
    Index("idx_kit_container", "kit", "container", unique=True),
)


@dataclass(eq=False, repr=False)
class SQLCreator:
    types: dict[str, str]
    qualities: dict[str, dict[str, str]]
    definitions: dict[str, dict[str, Any]]
    paints: dict[str, dict[str, Any]]
    musics: dict[str, dict[str, str]]
    rarities: dict[str, dict[str, Any]]
    containers: dict[str, dict[str, Any]]
    sticker_kit_containers: dict[str, dict[str, Any]]
    items: dict[str, dict[str, Any]]
    sticker_kits: dict[str, dict[str, Any]]
    music_kits: dict[str, dict[str, Any]]
    tints: dict[str, dict[str, str]]
    phases: dict[str, str]
    origins: dict[str, str]
    wears: list[dict[str, Any]]

    dialect: Dialect = field(default_factory=sqlite.dialect)

    def _create_expression(self) -> list[tuple[str, str]]:
        # create 'create' scripts

        scripts = []
        for dialect, file_suffix in [
            (postgresql.dialect(), "postgre"),
            (mysql.dialect(), "mysql"),
            (sqlite.dialect(), "sqlite"),
            (mssql.dialect(), "mssql"),
            (oracle.dialect(), "oracle"),
        ]:
            file = f"create_{file_suffix}.sql"

            script_arr: list[str] = []

            def dump(
                sql: TypeEngine,
                *multiparams: Any,
                dialect: Dialect = dialect,
                script_arr: list[str] = script_arr,
                **params: Any,
            ) -> None:
                exp = sql.compile(dialect=dialect)
                script_arr.append(str(exp))

            engine = create_mock_engine("sqlite:///:memory:", dump)
            metadata.create_all(engine, checkfirst=False)

            script_arr.append("\n")

            script_joined = ";".join(script_arr)
            scripts.append((file, script_joined))

        return scripts

    def _base_field(self, table: Table, source: Mapping[str, str | dict[str, str]]) -> list[str]:
        statements = []
        for type_id, type_data in source.items():
            if isinstance(type_data, dict):
                # Handle new dict structure with Chinese support
                values: dict[str, Any] = {"id": int(type_id)}
                for key, value in type_data.items():
                    values[key] = value
                statements.append(
                    table.insert()
                    .values(**values)
                    .compile(dialect=self.dialect, compile_kwargs={"literal_binds": True})
                    .string
                )
            else:
                # Handle old string structure (backward compatibility)
                statements.append(
                    table.insert()
                    .values(id=int(type_id), name=type_data)
                    .compile(dialect=self.dialect, compile_kwargs={"literal_binds": True})
                    .string
                )

        return statements

    def _populate_base_fields(self) -> tuple[list[str], list[str], list[str], list[str], list[str], list[str]]:
        types = self._base_field(Types, self.types)
        origins = self._base_field(Origins, self.origins)
        musics = self._base_field(Musics, self.musics)
        qualities = self._base_field(Qualities, self.qualities)
        phases = self._base_field(Phases, self.phases)
        tints = self._base_field(Tints, self.tints)

        return types, origins, musics, qualities, phases, tints

    def _populate_rarities(self) -> list[str]:
        rarities = []
        for rarity_id, rarity_data in self.rarities.items():
            rarities.append(
                Rarities.insert()
                .values(id=int(rarity_id), **rarity_data)
                .compile(dialect=self.dialect, compile_kwargs={"literal_binds": True})
                .string
            )

        return rarities

    def _populate_wears(self) -> list[str]:
        wears = []
        for wear_data in self.wears:
            wears.append(
                Wears.insert()
                .values(**wear_data)
                .compile(dialect=self.dialect, compile_kwargs={"literal_binds": True})
                .string
            )

        return wears

    def _populate_defs(self) -> list[str]:
        defs = []
        for defindex, def_data in self.definitions.items():
            defs.append(
                Definitions.insert()
                .values(
                    defindex=int(defindex),
                    type=int(def_data["type"]),
                    quality=int(def_data["quality"]) if "quality" in def_data else None,
                    rarity=int(def_data["rarity"]) if "rarity" in def_data else None,
                    name=def_data["name"],
                )
                .compile(dialect=self.dialect, compile_kwargs={"literal_binds": True})
                .string
            )

        return defs

    def _populate_paints(self) -> list[str]:
        paints = []
        for paintindex, paint_data in self.paints.items():
            paints.append(
                Paints.insert()
                .values(
                    paintindex=int(paintindex),
                    phase=int(paint_data["phase"]) if "phase" in paint_data else None,
                    rarity=int(paint_data["rarity"]),
                    name=paint_data["name"],
                    name_zh=paint_data.get("name_zh"),
                    wear_min=paint_data["wear_min"],
                    wear_max=paint_data["wear_max"],
                )
                .compile(dialect=self.dialect, compile_kwargs={"literal_binds": True})
                .string
            )

        return paints

    def _populate_items(self) -> list[str]:
        items = []
        for item_id, item_data in self.items.items():
            items.append(
                Items.insert()
                .values(
                    id=item_id,
                    **{"def": int(item_data["def"])},  # lol
                    paint=int(item_data["paint"]) if "paint" in item_data else None,
                    image=item_data.get("image"),
                )
                .compile(dialect=self.dialect, compile_kwargs={"literal_binds": True})
                .string
            )

        return items

    def _populate_sticker_kits(self) -> list[str]:
        sticker_kits = []
        for sticker_kits_id, sticker_kits_data in self.sticker_kits.items():
            sticker_kits.append(
                StickerKits.insert()
                .values(
                    id=int(sticker_kits_id),
                    rarity=int(sticker_kits_data["rarity"]) if "rarity" in sticker_kits_data else None,
                    name=sticker_kits_data["name"],
                    name_zh=sticker_kits_data.get("name_zh"),
                )
                .compile(dialect=self.dialect, compile_kwargs={"literal_binds": True})
                .string
            )

        return sticker_kits

    def _populate_containers(self) -> tuple[list[str], list[str]]:
        containers = []
        junctions = []
        for defindex, cont_data in self.containers.items():
            containers.append(
                Containers.insert()
                .values(
                    defindex=int(defindex),
                    set=cont_data.get("set"),
                    associated=int(cont_data["associated"]) if "associated" in cont_data else None,
                )
                .compile(dialect=self.dialect, compile_kwargs={"literal_binds": True})
                .string
            )

            for item_id in cont_data["items"]:
                junctions.append(
                    ItemsContainersJunction.insert()
                    .values(
                        item=item_id,
                        container=int(defindex),
                    )
                    .compile(dialect=self.dialect, compile_kwargs={"literal_binds": True})
                    .string
                )

        return containers, junctions

    def _populate_sticker_kit_containers(self) -> tuple[list[str], list[str]]:
        containers = []
        junctions = []
        for defindex, cont_data in self.sticker_kit_containers.items():
            containers.append(
                StickerKitContainers.insert()
                .values(
                    defindex=int(defindex),
                )
                .compile(dialect=self.dialect, compile_kwargs={"literal_binds": True})
                .string
            )

            for item_id in cont_data["kits"]:
                junctions.append(
                    StickerKitsContainersJunction.insert()
                    .values(
                        kit=int(item_id),
                        container=int(defindex),
                    )
                    .compile(dialect=self.dialect, compile_kwargs={"literal_binds": True})
                    .string
                )

        return containers, junctions

    def _populate_music_kits(self) -> tuple[list[str], list[str]]:
        containers = []
        junctions = []
        for defindex, cont_data in self.music_kits.items():
            containers.append(
                MusicKits.insert()
                .values(
                    defindex=int(defindex),
                )
                .compile(dialect=self.dialect, compile_kwargs={"literal_binds": True})
                .string
            )

            for item_id in cont_data["musics"]:
                junctions.append(
                    MusicsMusicKitsJunction.insert()
                    .values(
                        music=int(item_id),
                        container=int(defindex),
                    )
                    .compile(dialect=self.dialect, compile_kwargs={"literal_binds": True})
                    .string
                )

        return containers, junctions

    def create(self) -> list[tuple[str, str]]:
        create_scripts = self._create_expression()

        types, origins, musics, qualities, phases, tints = self._populate_base_fields()

        rarities = self._populate_rarities()
        wears = self._populate_wears()
        defs = self._populate_defs()
        paints = self._populate_paints()

        items = self._populate_items()
        sticker_kits = self._populate_sticker_kits()

        containers, items_junc = self._populate_containers()
        sticker_kit_container, stick_junc = self._populate_sticker_kit_containers()
        music_kits, music_junc = self._populate_music_kits()

        populate = ";\n".join(
            [
                *types,
                *origins,
                *musics,
                *qualities,
                *phases,
                *tints,
                *rarities,
                *wears,
                *defs,
                *paints,
                *items,
                *sticker_kits,
                *containers,
                *items_junc,
                *music_kits,
                *music_junc,
                *sticker_kit_container,
                *stick_junc,
            ]
        )

        return [*create_scripts, ("populate.sql", populate + ";\n")]
