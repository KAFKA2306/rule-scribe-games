import asyncio
import os
import json
from dotenv import load_dotenv
from app.services.gemini_client import GeminiClient

# Load environment variables
load_dotenv()

async def verify_generation():
    client = GeminiClient()
    query = "Azul"
    print(f"Generating data for: {query}")
    
    result = await client.extract_game_info(query)
    
    print("\n--- Generated Data ---")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    # Basic verification checks
    if "error" in result:
        print("\n[FAILED] Generation returned an error.")
    else:
        required_fields = ["title", "title_ja", "description", "rules_content"]
        missing_fields = [f for f in required_fields if f not in result]
        
        if missing_fields:
            print(f"\n[FAILED] Missing fields: {missing_fields}")
        else:
            print("\n[SUCCESS] Generation structure looks correct.")
            
        if "_debug_info" in result:
            print(f"\nDebug Info: {result['_debug_info']}")

if __name__ == "__main__":
    asyncio.run(verify_generation())
