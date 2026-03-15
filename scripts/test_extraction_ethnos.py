import asyncio
import logging
import sys
import os

# Change to backend directory to ensure relative paths work
os.chdir(os.path.join(os.getcwd(), "backend"))
sys.path.append(os.getcwd())

from app.services.pipeline_orchestrator import PipelineOrchestrator
from app.core.logger import setup_logging

async def test_ethnos_extraction():
    setup_logging()
    logger = logging.getLogger("test_ethnos")
    
    orchestrator = PipelineOrchestrator()
    game_title = "Ethnos"
    
    print(f"🚀 Starting extraction test for: {game_title}")
    
    try:
        result = await orchestrator.process_game_rules(game_title)
        print("\n✅ Extraction Successful!")
        print(f"Title: {result.get('title_ja')}")
        print(f"Summary: {result.get('summary')[:100]}...")
        # print(f"Rules: {result.get('rules_content')[:200]}...")
    except Exception as e:
        print(f"\n❌ Extraction Failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_ethnos_extraction())
