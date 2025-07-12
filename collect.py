import argparse
import asyncio
import getpass
import logging
from pathlib import Path

from src.config import Settings
from src.core import ResourceCollector
from src.services.auto_downloader import AutoDownloader
from src.services.item_formatter import ItemFormatterService


def setup_logging() -> None:
    """Configure logging for the application."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),
        ],
    )


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="CS2 Items Schema Collector")
    parser.add_argument("--local", action="store_true", help="Use local files instead of downloading from remote URLs")
    parser.add_argument(
        "--local-dir", type=Path, default=Path("static"), help="Directory containing local game files (default: static)"
    )
    parser.add_argument("--download-demo", action="store_true", help="Download demo files for testing")
    parser.add_argument(
        "--steam-login",
        metavar="USERNAME",
        help="Download using Steam login (will prompt for password securely)",
    )
    parser.add_argument("--steam-2fa", help="Steam 2FA code (for use with --steam-login)")
    parser.add_argument(
        "--save-raw", action="store_true", help="Save raw game files to static/ directory when using remote mode"
    )

    return parser.parse_args()


if __name__ == "__main__":
    setup_logging()
    args = parse_args()

    # Handle auto-download options
    if args.download_demo or args.steam_login:
        downloader = AutoDownloader(static_dir=args.local_dir)

        if args.download_demo:
            logging.info("Downloading demo files...")
            if downloader.download_demo_files():
                logging.info("Demo files downloaded successfully")
            else:
                logging.error("Failed to download demo files")
                exit(1)

        elif args.steam_login:
            username = args.steam_login
            password = getpass.getpass("Enter your Steam password: ")
            two_factor_code = args.steam_2fa

            logging.info("Downloading files using Steam login...")
            if downloader.download_with_steam_login(username, password, two_factor_code):
                logging.info("Steam download completed successfully")
            else:
                logging.error("Steam download failed")
                exit(1)

    # Create settings with local file support
    settings = Settings()

    # Create collector with local file support if requested
    if args.local:
        from src.services.data_fetcher import DataFetcher

        # Override the data fetcher to use local files
        collector = ResourceCollector(settings)
        collector.data_fetcher = DataFetcher(
            urls=settings.urls, timeout=settings.request_timeout, use_local_files=True, local_dir=args.local_dir
        )
        logging.info(f"Using local files from: {args.local_dir}")
    else:
        collector = ResourceCollector(settings)
        # Override data fetcher if save-raw is requested
        if args.save_raw:
            from src.services.data_fetcher import DataFetcher

            collector.data_fetcher = DataFetcher(
                urls=settings.urls,
                timeout=settings.request_timeout,
                use_local_files=False,
                local_dir=args.local_dir,
                save_raw_files=True,
            )
            logging.info("Using remote URLs with raw file saving enabled")
        else:
            logging.info("Using remote URLs for data fetching")

    try:
        asyncio.run(collector.collect())

        # 数据收集完成后，自动格式化物品数据
        logging.info("Starting item formatting...")
        formatter = ItemFormatterService(schemas_dir="schemas")
        formatted_items = formatter.save_formatted_items()
        logging.info(f"Item formatting completed. {len(formatted_items)} items processed.")

    except KeyboardInterrupt:
        logging.info("Collection interrupted by user")
    except Exception as e:
        logging.error(f"Collection failed: {e}")
        raise
