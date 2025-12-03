import asyncio
import time
import os
from app.services.gemini_client import GeminiClient
from app.core.setup import apply_initial_setup
from pathlib import Path
from dotenv import load_dotenv

async def benchmark():
    env_path = Path("backend/.env").resolve()
    print(f"Loading env from: {env_path}, exists: {env_path.exists()}")
    load_dotenv(env_path)
    
    client = GeminiClient()
    
    queries = [
        "Heart of Crown 2nd Edition",
        "The White Castle",
        "Terraforming Mars"
    ]
    
    print(f"{'Query':<30} | {'Time (s)':<10} | {'Status':<10}")
    print("-" * 55)
    
    for query in queries:
        start_time = time.time()
        try:
            result = await client.extract_game_info(query)
            duration = time.time() - start_time
            status = "OK" if "error" not in result else "Error"
            print(f"{query:<30} | {duration:<10.2f} | {status:<10}")
        except Exception as e:
            duration = time.time() - start_time
            print(f"{query:<30} | {duration:<10.2f} | Failed: {e}")

if __name__ == "__main__":
    asyncio.run(benchmark())
