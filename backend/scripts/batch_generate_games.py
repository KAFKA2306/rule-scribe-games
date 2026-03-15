import asyncio
import os
import sys
import logging

from dotenv import load_dotenv

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.game_service import GameService

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

GAMES_TO_GENERATE = [
    "Sweetland",
    "The Wolves",
    "Desolati",
    "Steam Power",
    "Ethnos",
    "Bean to Bar",
    "Libertalia",
]

async def main():
    """
    Main function to generate games in batch.
    """
    service = GameService()
    logging.info("Starting batch generation for %d games.", len(GAMES_TO_GENERATE))

    for game_name in GAMES_TO_GENERATE:
        logging.info("--- Generating game: %s ---", game_name)
        try:
            # The generate_with_notebooklm function already handles the investigation,
            # generation, and adding to Supabase.
            result = await service.generate_with_notebooklm(game_name)
            if result and result.get("slug"):
                logging.info("SUCCESS: Generated and upserted '%s' with slug '%s'", game_name, result.get("slug"))
            else:
                logging.error("FAILED: Did not receive a valid result for '%s'. Result: %s", game_name, result)
        except Exception as e:
            logging.error("ERROR: An exception occurred while processing '%s': %s", game_name, e, exc_info=True)
        logging.info("--- Finished game: %s ---", game_name)

    logging.info("Batch generation process completed.")

if __name__ == "__main__":
    asyncio.run(main())
