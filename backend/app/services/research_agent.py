from typing import List, Dict, Any
import os
import json
from crewai import Agent, Task, Crew, Process
from crewai_tools import tool
from app.core.supabase import supabase_repository
import anyio

SCHEMA_DESCRIPTION = """
Table: games
Columns:

id: integer primary key
slug: unique string identifier (e.g., 'catan', 'ticket-to-ride')
title: English or original name
title_ja: Japanese name
summary: short Japanese summary
rules_content: full rules in Markdown or text
bgg_url: BoardGameGeek URL
min_players: minimum number of players
max_players: maximum number of players
play_time: play time in minutes
min_age: minimum age
published_year: year published
"""

@tool("schema_search")
def schema_search_tool(query: str) -> str:
    """
    Search the existing games database for relevant information.
    Useful for checking if a game already exists or finding similar games.
    """
    # Since tools are synchronous in CrewAI (mostly), we need to run the async repo method synchronously
    # or use a synchronous client if available. Here we use anyio.run to bridge.
    # CAUTION: Nesting async loops can be tricky.
    # For simplicity in this specific environment, we might need a sync wrapper.
    
    async def _do_search():
        # We use the existing repository's search method
        results = await supabase_repository.search(query)
        return results

    try:
        # Check if there is a running loop, if so, we might need to use it or run in thread
        # But CrewAI tools run in a thread usually.
        # Let's try a simple approach:
        rows = anyio.run(_do_search)
    except RuntimeError:
        # If we are already in a loop (which we likely are if called from async FastAPI -> CrewAI)
        # We might need to just use the sync client directly if possible, or accept that
        # CrewAI might block.
        # However, CrewAI often runs in its own thread/process logic.
        # Let's assume for now we can use a fresh loop or it's called from a thread.
        # Actually, `anyio.run` creates a new loop.
        # If we are in a thread, this is fine.
        rows = anyio.run(_do_search)

    if not rows:
        return "No results found."

    parts = []
    for i, r in enumerate(rows, 1):
        parts.append(
            f"[{i}] slug={r.get('slug')}\n"
            f"title={r.get('title')} / {r.get('title_ja')}\n"
            f"summary={r.get('summary')}\n"
            f"rules_content={str(r.get('rules_content'))[:500]}...\n"
            f"url={r.get('bgg_url')}\n"
        )
    return "\n\n".join(parts)

class ResearchAgentService:
    def __init__(self):
        self.model_name = "gemini/gemini-2.5-flash" # CrewAI format for Gemini
        # Ensure API key is set for CrewAI (it looks for GOOGLE_API_KEY usually, or GEMINI_API_KEY)
        if not os.getenv("GOOGLE_API_KEY") and os.getenv("GEMINI_API_KEY"):
            os.environ["GOOGLE_API_KEY"] = os.getenv("GEMINI_API_KEY")

    def run_research_task(self, query: str) -> Dict[str, Any]:
        """
        Run the iterative research task to generate/update game data.
        Returns a dictionary with the structured game data.
        """
        
        researcher = Agent(
            role="Board Game Researcher",
            goal="Produce accurate and comprehensive board game information in JSON format.",
            backstory=(
                "You are an expert board game archivist. "
                "You have access to a database of existing games via the schema_search tool. "
                "Your job is to research a specific game and produce a final JSON output "
                "that matches the database schema. "
                "You should verify facts and ensure the Japanese translation is natural."
            ),
            tools=[schema_search_tool],
            verbose=True,
            memory=False, # Stateless for now
            llm=self.model_name
        )

        # Task to generate the content
        task = Task(
            description=(
                f"Research the board game '{query}'.\n"
                "1. Search for existing information if needed using schema_search.\n"
                "2. Compile all details: title, title_ja, summary (Japanese), rules_content (Markdown), "
                "min_players, max_players, play_time, min_age, published_year, bgg_url.\n"
                "3. Ensure 'summary' is a catchy, accurate Japanese description.\n"
                "4. Ensure 'rules_content' is a helpful summary of the rules in Japanese Markdown.\n"
                "5. Return the result strictly as a valid JSON object."
            ),
            expected_output="A valid JSON object containing the game fields.",
            agent=researcher
        )

        crew = Crew(
            agents=[researcher],
            tasks=[task],
            process=Process.sequential
        )

        result = crew.kickoff()
        
        # Parse the result string into JSON
        # CrewAI returns a string (TaskOutput.raw)
        try:
            # Clean up markdown code blocks if present
            cleaned = str(result).strip()
            if "```json" in cleaned:
                import re
                match = re.search(r"```json\s*(.*?)\s*```", cleaned, re.DOTALL)
                if match:
                    cleaned = match.group(1)
            elif "```" in cleaned:
                 match = re.search(r"```\s*(.*?)\s*```", cleaned, re.DOTALL)
                 if match:
                    cleaned = match.group(1)
            
            return json.loads(cleaned)
        except Exception as e:
            print(f"Failed to parse CrewAI result: {e}")
            print(f"Raw result: {result}")
            return {"error": "Failed to generate valid JSON", "raw": str(result)}
