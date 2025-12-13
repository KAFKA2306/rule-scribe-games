import sys
import asyncio
import time
from pathlib import Path

# Add project root to sys.path
project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from app.services.game_service import generate_metadata


async def main():
    query = "Terraforming Mars"
    print(f"Testing generate_metadata with query: {query}")
    start = time.time()
    try:
        data = await generate_metadata(query)
        elapsed = time.time() - start
        print(f"--- SUCCESS in {elapsed:.2f}s ---")
        # print(data) # Reduce noise
    except Exception as e:
        elapsed = time.time() - start
        print(f"--- CRASH in {elapsed:.2f}s ---")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
