"""
Example: Safe batch update script using the fixed patterns.
This script demonstrates how to safely process 50+ games without connection pool exhaustion.
"""

import asyncio
import sys
import os

sys.path.append(os.getcwd())

from app.services.game_service import GameService
from app.services.batch_processor import batch_process_with_retry
from app.core import logger

# Define games to update (example)
GAMES_TO_UPDATE = [
    "catan",
    "ticket-to-ride",
    "carcassonne",
    "splendor",
    "azul",
    "wingspan",
    "everdell",
    "oink-games-title",
    "codenames",
    "dixit",
    # Add more slugs as needed, up to 50+
]


async def process_single_game(service: GameService, slug: str) -> dict:
    """Process a single game update."""
    try:
        result = await service.update_game_content(slug, fill_missing_only=True)
        logger.info(f"✅ {slug} updated successfully")
        return {"slug": slug, "status": "success", "data": result}
    except Exception as e:
        logger.error(f"❌ {slug} failed: {e}")
        raise


async def main():
    """Main batch processing function."""
    service = GameService()

    logger.info(f"Starting batch update for {len(GAMES_TO_UPDATE)} games")

    # Use batch processor with retry for resilience
    successes, failures = await batch_process_with_retry(
        items=GAMES_TO_UPDATE,
        process_fn=lambda slug: process_single_game(service, slug),
        batch_size=5,  # Process 5 games at a time
        delay_between_batches=0.5,  # 500ms delay between batches
        max_retries=3,  # Retry up to 3 times per game
    )

    logger.info(f"\n=== RESULTS ===")
    logger.info(f"Succeeded: {len(successes)}")
    logger.info(f"Failed: {len(failures)}")

    if failures:
        logger.warning(f"Failed games: {failures}")
        return 1
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
