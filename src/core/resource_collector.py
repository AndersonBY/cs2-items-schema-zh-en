"""Main resource collector orchestrating the data collection process."""

import logging
from typing import Any

from ..collectors import FieldsCollector
from ..config import Settings
from ..exceptions import CS2SchemaError
from ..services import DataFetcher, FileManager
from ..sql import SQLCreator

logger = logging.getLogger(__name__)


class ResourceCollector:
    """Main orchestrator for collecting and processing CS2 item schema data."""

    def __init__(self, settings: Settings | None = None):
        self.settings = settings or Settings()
        self.data_fetcher = DataFetcher(self.settings.urls, timeout=self.settings.request_timeout)
        self.file_manager = FileManager(self.settings)

    async def collect(self) -> None:
        """Main collection process."""
        try:
            logger.info("Starting CS2 schema data collection")

            # Load required schema files
            logger.info("Loading required schema files")
            schemas = self.file_manager.load_required_schemas()

            # Fetch game data
            logger.info("Fetching game data from external sources")
            game_data = await self.data_fetcher.fetch_all_data()

            # Process fields data
            logger.info("Processing field data")
            fields_collector = FieldsCollector(game_data, schemas["phasesmapping"])
            types, qualities, definitions, paints, rarities, musics, tints = fields_collector.collect()

            # TODO: Process containers, items, and sticker kits
            # For now, create empty collections to maintain structure
            containers = {}
            sticker_kit_containers = {}
            items = {}
            sticker_kits = {}
            music_kits = {}

            logger.info("Preparing data for export")
            json_files = self._prepare_json_files(
                types,
                qualities,
                definitions,
                paints,
                rarities,
                musics,
                tints,
                containers,
                sticker_kit_containers,
                items,
                sticker_kits,
                music_kits,
            )

            # Generate SQL files
            logger.info("Generating SQL files")
            sql_creator = SQLCreator(
                types=types,
                qualities=qualities,
                definitions=definitions,
                paints=paints,
                rarities=rarities,
                musics=musics,
                tints=tints,
                containers=containers,
                sticker_kit_containers=sticker_kit_containers,
                items=items,
                sticker_kits=sticker_kits,
                music_kits=music_kits,
                phases=schemas["phases"],
                wears=schemas["wears"],
                origins=schemas["origins"],
            )
            sql_files = sql_creator.create()

            # Save all files
            logger.info("Saving JSON and SQL files")
            self.file_manager.save_json_files(*json_files)
            self.file_manager.save_text_files(*sql_files)

            logger.info("CS2 schema data collection completed successfully")

        except CS2SchemaError:
            logger.error("Collection failed due to application error", exc_info=True)
            raise
        except Exception as e:
            logger.error("Collection failed due to unexpected error", exc_info=True)
            raise CS2SchemaError(f"Unexpected error during collection: {e}") from e

    def _prepare_json_files(
        self,
        types: dict[str, str],
        qualities: dict[str, dict[str, str]],
        definitions: dict[str, dict[str, Any]],
        paints: dict[str, dict[str, Any]],
        rarities: dict[str, dict[str, Any]],
        musics: dict[str, dict[str, str]],
        tints: dict[str, dict[str, str]],
        containers: dict[str, Any],
        sticker_kit_containers: dict[str, Any],
        items: dict[str, Any],
        sticker_kits: dict[str, Any],
        music_kits: dict[str, Any],
    ) -> list[tuple[str, dict | list]]:
        """Prepare list of files to be saved as JSON."""
        return [
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
