"""Data fetching service for external resources."""

import asyncio

import aiohttp
import vdf
from multidict import CIMultiDict

from ..config import DataUrls
from ..exceptions import DataFetchError
from ..models.types import GameData


class DataFetcher:
    """Service for fetching game data from external sources."""

    def __init__(self, urls: DataUrls, timeout: int = 30):
        self.urls = urls
        self.timeout = timeout

    async def fetch_all_data(self) -> GameData:
        """Fetch all required game data concurrently."""
        try:
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

                return self._parse_responses(items_game_raw, csgo_english_raw, csgo_schinese_raw, items_cdn_raw)

        except aiohttp.ClientError as e:
            raise DataFetchError(f"Network error during data fetch: {e}") from e
        except Exception as e:
            raise DataFetchError(f"Unexpected error during data fetch: {e}") from e

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
