"""Data source URLs configuration."""

from dataclasses import dataclass


@dataclass(frozen=True)
class DataUrls:
    """Data source URLs for CS2 game files."""

    BASE_URL: str = "https://raw.githubusercontent.com/AndersonBY/cs-files-zh-en/master/static"

    @property
    def items_game_url(self) -> str:
        return f"{self.BASE_URL}/items_game.txt"

    @property
    def csgo_english_url(self) -> str:
        return f"{self.BASE_URL}/csgo_english.txt"

    @property
    def csgo_schinese_url(self) -> str:
        return f"{self.BASE_URL}/csgo_schinese.txt"

    @property
    def items_game_cdn_url(self) -> str:
        return f"{self.BASE_URL}/items_game_cdn.txt"

    def get_all_urls(self) -> list[str]:
        """Get all data URLs as a list."""
        return [
            self.items_game_url,
            self.csgo_english_url,
            self.csgo_schinese_url,
            self.items_game_cdn_url,
        ]
