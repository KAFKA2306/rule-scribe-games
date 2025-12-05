import asyncio
import json
import sys
import os

# Ensure we can import from app
sys.path.append(os.getcwd())

from app.services.research_agent import ResearchAgentService

def main():
    print("Initializing ResearchAgentService...")
    try:
        service = ResearchAgentService()
    except Exception as e:
        print(f"Failed to initialize service: {e}")
        return

    query = "Catan"
    print(f"Running research task for: {query}")
    print("This may take a minute...")

    try:
        # run_research_task is synchronous (it runs CrewAI which blocks)
        # But inside it might use anyio.run for async tools.
        # Since we are in a sync main, this is fine.
        result = service.run_research_task(query)
        
        print("\n=== Verification Result ===")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        print("===========================")
        
        # Check for concrete fields
        if result.get("summary") and result.get("rules_content"):
            print("\nSUCCESS: Generated concrete summary and rules.")
        else:
            print("\nWARNING: Some fields might be missing.")

    except Exception as e:
        print(f"\nERROR: Research task failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
