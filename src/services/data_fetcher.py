"""Data fetching service for external resources."""

import asyncio
from pathlib import Path

import aiohttp
import vdf
from multidict import CIMultiDict

from ..config import DataUrls
from ..exceptions import DataFetchError
from ..models.types import GameData
from .auto_downloader import AutoDownloader


class DataFetcher:
    """Service for fetching game data from external sources."""

    def __init__(self, urls: DataUrls, timeout: int = 30, use_local_files: bool = False, local_dir: Path | None = None, save_raw_files: bool = False):
        self.urls = urls
        self.timeout = timeout
        self.use_local_files = use_local_files
        self.save_raw_files = save_raw_files
        self.auto_downloader = AutoDownloader(static_dir=local_dir or Path("static"))

    async def fetch_all_data(self) -> GameData:
        """Fetch all required game data concurrently."""
        try:
            if self.use_local_files:
                return await self._fetch_local_data()
            else:
                return await self._fetch_remote_data()
        except Exception as e:
            raise DataFetchError(f"Unexpected error during data fetch: {e}") from e

    async def _fetch_remote_data(self) -> GameData:
        """Fetch data from remote URLs."""
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
            tasks = [self._fetch_url(session, url) for url in self.urls.get_all_urls()]

            responses = await asyncio.gather(*tasks, return_exceptions=True)

            # Check for exceptions
            for i, response in enumerate(responses):
                if isinstance(response, Exception):
                    raise DataFetchError(
                        f"Failed to fetch data from {self.urls.get_all_urls()[i]}", details={"error": str(response)}
                    )

            # All responses are strings after exception check
            items_game_raw, csgo_english_raw, csgo_schinese_raw, items_cdn_raw = (str(r) for r in responses)

            # Optionally save raw files for debugging/caching
            if self.save_raw_files:
                await self._save_raw_files(items_game_raw, csgo_english_raw, csgo_schinese_raw, items_cdn_raw)

            return self._parse_responses(items_game_raw, csgo_english_raw, csgo_schinese_raw, items_cdn_raw)

    async def _fetch_local_data(self) -> GameData:
        """Fetch data from local files."""
        # Check if update is needed
        if self.auto_downloader.is_update_needed():
            # Try to download demo files first
            if not self.auto_downloader.download_demo_files():
                raise DataFetchError("Failed to create demo files")

        # Get local file paths
        file_paths = self.auto_downloader.get_local_files_path()

        # Read local files
        try:
            items_game_raw = file_paths["items_game"].read_text(encoding="utf-8")
            csgo_english_raw = file_paths["csgo_english"].read_text(encoding="utf-8")
            csgo_schinese_raw = file_paths["csgo_schinese"].read_text(encoding="utf-8")
            items_cdn_raw = file_paths["items_cdn"].read_text(encoding="utf-8")

            return self._parse_responses(items_game_raw, csgo_english_raw, csgo_schinese_raw, items_cdn_raw)

        except FileNotFoundError as e:
            raise DataFetchError(f"Local file not found: {e}") from e
        except UnicodeDecodeError as e:
            raise DataFetchError(f"Failed to decode local file: {e}") from e

    async def _fetch_url(self, session: aiohttp.ClientSession, url: str) -> str:
        """Fetch content from a single URL."""
        async with session.get(url) as response:
            response.raise_for_status()
            return await response.text()

    def _parse_responses(
        self, items_game_raw: str, csgo_english_raw: str, csgo_schinese_raw: str, items_cdn_raw: str
    ) -> GameData:
        """Parse raw response data into structured format."""
        try:
            # Parse VDF data
            items_game = vdf.loads(items_game_raw)["items_game"]
            csgo_english: CIMultiDict[str] = CIMultiDict(vdf.loads(csgo_english_raw)["lang"]["Tokens"])
            csgo_schinese: CIMultiDict[str] = CIMultiDict(vdf.loads(csgo_schinese_raw)["lang"]["Tokens"])

            # Parse CDN data
            items_cdn = self._parse_cdn_data(items_cdn_raw)

            return GameData(
                items_game=items_game, csgo_english=csgo_english, csgo_schinese=csgo_schinese, items_cdn=items_cdn
            )

        except Exception as e:
            raise DataFetchError(f"Failed to parse game data: {e}") from e

    def _parse_cdn_data(self, cdn_raw: str) -> dict[str, str]:
        """Parse CDN data from raw text."""
        try:
            lines = cdn_raw.splitlines()[3:]  # Skip first 3 lines
            return dict(line.split("=", 1) for line in lines if "=" in line)
        except Exception as e:
            raise DataFetchError(f"Failed to parse CDN data: {e}") from e

    async def _save_raw_files(self, items_game_raw: str, csgo_english_raw: str, csgo_schinese_raw: str, items_cdn_raw: str) -> None:
        """Save raw game files to local directory for caching/debugging."""
        try:
            import logging
            logger = logging.getLogger(__name__)

            # Ensure static directory exists
            self.auto_downloader.ensure_directories()

            # Save each file
            files_to_save = [
                ("items_game.txt", items_game_raw),
                ("csgo_english.txt", csgo_english_raw),
                ("csgo_schinese.txt", csgo_schinese_raw),
                ("items_game_cdn.txt", items_cdn_raw),
            ]

            for filename, content in files_to_save:
                file_path = self.auto_downloader.static_dir / filename
                file_path.write_text(content, encoding="utf-8")
                logger.info(f"Saved raw file: {file_path}")

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to save raw files: {e}")
