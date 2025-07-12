"""Auto downloader service for CS2 game files."""

import logging
import time
from pathlib import Path

logger = logging.getLogger(__name__)


class AutoDownloader:
    """Automated downloader for CS2 game files using local Steam access."""

    def __init__(self, static_dir: Path = Path("static"), temp_dir: Path = Path("temp")):
        self.static_dir = static_dir
        self.temp_dir = temp_dir
        self.app_id = 730
        self.depot_id = 2347770

        # Target files to extract
        self.target_files = [
            "resource/csgo_english.txt",
            "resource/csgo_schinese.txt",
            "scripts/items/items_game.txt",
        ]

    def ensure_directories(self) -> None:
        """Create necessary directories if they don't exist."""
        self.static_dir.mkdir(exist_ok=True)
        self.temp_dir.mkdir(exist_ok=True)

    def download_demo_files(self) -> bool:
        """
        Download demo files without Steam login (for testing).

        Returns:
            True if successful, False otherwise
        """
        logger.info("Creating demo CS:GO files...")

        try:
            self.ensure_directories()

            files_to_create = [
                {"name": "csgo_english.txt", "description": "English localization file"},
                {"name": "csgo_schinese.txt", "description": "Chinese localization file"},
                {"name": "items_game.txt", "description": "Game items definition file"},
                {"name": "items_game_cdn.txt", "description": "CDN items info"},
            ]

            for file_info in files_to_create:
                filename = file_info["name"]
                filepath = self.static_dir / filename

                logger.info(f"Creating sample {filename}...")

                if filename == "csgo_english.txt":
                    content = """// Counter-Strike: Global Offensive English Text
"lang"
{
    "Language"      "english"
    "Tokens"
    {
        "CSGO_Watch_Nav_Overwatch"    "Overwatch"
        "CSGO_Watch_Nav_YourMatches"  "Your Matches"
        "CSGO_MainMenu_PlayButton"    "PLAY"
        "CSGO_MainMenu_WatchButton"   "WATCH"
        "weapon_deagle"               "Desert Eagle"
        "weapon_ak47"                 "AK-47"
    }
}"""
                elif filename == "csgo_schinese.txt":
                    content = """// Counter-Strike: Global Offensive Chinese Text
"lang"
{
    "Language"      "schinese"
    "Tokens"
    {
        "CSGO_Watch_Nav_Overwatch"    "监管者"
        "CSGO_Watch_Nav_YourMatches"  "你的比赛"
        "CSGO_MainMenu_PlayButton"    "开始游戏"
        "CSGO_MainMenu_WatchButton"   "观看"
        "weapon_deagle"               "沙漠之鹰"
        "weapon_ak47"                 "AK-47"
    }
}"""
                elif filename == "items_game.txt":
                    content = """"items_game"
{
    "items"
    {
        "1"
        {
            "name"              "weapon_deagle"
            "prefab"            "weapon_base"
            "item_class"        "weapon"
            "item_type_name"    "Pistol"
            "item_name"         "Desert Eagle"
        }
        "2"
        {
            "name"              "weapon_ak47"
            "prefab"            "weapon_base"
            "item_class"        "weapon"
            "item_type_name"    "Rifle"
            "item_name"         "AK-47"
        }
    }
    "prefabs"
    {
        "weapon_base"
        {
            "item_class"        "weapon"
        }
    }
}"""
                elif filename == "items_game_cdn.txt":
                    content = """# CDN Information
# Manifest Version
# Version Info
deagle=weapon_deagle
ak47=weapon_ak47"""

                filepath.write_text(content, encoding="utf-8")
                size = filepath.stat().st_size
                logger.info(f"Created {filename}: {size:,} bytes")

            # Create manifest file
            manifest_file = self.static_dir / "manifestId.txt"
            manifest_id = str(int(time.time()))
            manifest_file.write_text(manifest_id)

            logger.info(f"Manifest ID: {manifest_id}")
            logger.info(f"Files saved to: {self.static_dir}")
            logger.info("Demo download completed successfully!")

            return True

        except Exception as e:
            logger.error(f"Demo download failed: {e}")
            return False

    def download_with_steam_login(self, username: str, password: str, two_factor_code: str | None = None) -> bool:
        """
        Download files using Steam login (requires steam library).

        Args:
            username: Steam username
            password: Steam password
            two_factor_code: Optional 2FA code

        Returns:
            True if successful, False otherwise
        """
        try:
            # Import Steam libraries (optional dependency)
            from steam.client import SteamClient  # type: ignore
            from steam.client.cdn import CDNClient  # type: ignore
            from steam.enums import EResult  # type: ignore
        except ImportError:
            logger.error("Steam library not available. Please install: pip install steam")
            return False

        logger.info("Downloading CS:GO files with Steam authentication...")

        try:
            self.ensure_directories()

            # Authenticate with Steam
            client = SteamClient()

            # Login process
            if two_factor_code:
                result = client.login(username, password, two_factor_code=two_factor_code)
            else:
                result = client.login(username, password)

            # Handle Steam Guard
            if result == EResult.AccountLogonDenied:
                logger.info("Steam Guard email authentication required.")
                email_code = input("Please enter your Steam Guard email code: ").strip()
                result = client.login(username, password, auth_code=email_code)
                if result != EResult.OK:
                    logger.error(f"Login failed: {result.name}")
                    return False
            elif result == EResult.AccountLoginDeniedNeedTwoFactor:
                logger.info("Mobile authenticator (2FA) code required.")
                return False
            elif result != EResult.OK:
                logger.error(f"Login failed: {result.name}")
                return False

            # Wait for login
            for _ in range(30):
                if client.logged_on:
                    break
                time.sleep(1)
            else:
                logger.error("Login timeout")
                return False

            logger.info("Steam login successful!")

            # Initialize CDN client
            cdn_client = CDNClient(client)

            # Get app info
            app_info = client.get_product_info(apps=[self.app_id])
            if not app_info or "apps" not in app_info:
                raise ValueError("Failed to get app info")

            cs_info = app_info["apps"][self.app_id]
            depot_info = cs_info["depots"][str(self.depot_id)]
            manifest_id = depot_info["manifests"]["public"]["gid"]

            logger.info(f"Latest manifest ID: {manifest_id}")

            # Get manifest
            manifest_request_code = cdn_client.get_manifest_request_code(self.app_id, self.depot_id, manifest_id)
            manifest = cdn_client.get_manifest(
                self.app_id, self.depot_id, manifest_id, manifest_request_code=manifest_request_code
            )

            # Extract files directly from manifest
            extracted_count = 0
            for file_info in manifest.iter_files():
                filename = file_info.filename.replace("\\", "/")

                for target_file in self.target_files:
                    if filename == target_file:
                        logger.info(f"Extracting {filename}...")

                        file_data = file_info.read()
                        save_filename = target_file.split("/")[-1]
                        save_path = self.static_dir / save_filename

                        save_path.write_bytes(file_data)
                        extracted_count += 1

            # Create CDN info file placeholder
            cdn_file = self.static_dir / "items_game_cdn.txt"
            cdn_file.write_text("# CDN Information extracted from Steam\n")

            # Save manifest ID
            manifest_file = self.static_dir / "manifestId.txt"
            manifest_file.write_text(str(manifest_id))

            logger.info(f"Successfully extracted {extracted_count} files")
            logger.info("Steam download completed successfully!")

            # Logout
            if hasattr(client, "logout"):
                client.logout()

            return True

        except Exception as e:
            logger.error(f"Steam download failed: {e}")
            return False

    def is_update_needed(self) -> bool:
        """
        Check if files need to be updated.

        Returns:
            True if update is needed, False otherwise
        """
        manifest_file = self.static_dir / "manifestId.txt"

        if not manifest_file.exists():
            return True

        # Check if all required files exist
        required_files = ["csgo_english.txt", "csgo_schinese.txt", "items_game.txt"]
        for filename in required_files:
            if not (self.static_dir / filename).exists():
                return True

        return False

    def get_local_files_path(self) -> dict[str, Path]:
        """
        Get paths to local game files.

        Returns:
            Dictionary mapping file types to their paths
        """
        return {
            "items_game": self.static_dir / "items_game.txt",
            "csgo_english": self.static_dir / "csgo_english.txt",
            "csgo_schinese": self.static_dir / "csgo_schinese.txt",
            "items_cdn": self.static_dir / "items_game_cdn.txt",
        }
