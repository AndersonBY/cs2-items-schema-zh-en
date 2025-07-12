import asyncio
import logging

from src.config import Settings
from src.core import ResourceCollector


def setup_logging() -> None:
    """Configure logging for the application."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),
        ],
    )


if __name__ == "__main__":
    setup_logging()

    settings = Settings()
    collector = ResourceCollector(settings)

    try:
        asyncio.run(collector.collect())
    except KeyboardInterrupt:
        logging.info("Collection interrupted by user")
    except Exception as e:
        logging.error(f"Collection failed: {e}")
        raise
