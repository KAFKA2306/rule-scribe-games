from typing import Dict, Any
import os
import json
from crewai import Agent, Task, Crew, Process
from crewai.tools import tool
from app.core.supabase import supabase_repository
import anyio

SCHEMA_DESCRIPTION = "\nTable: games\nColumns:\n\nid: integer primary key\nslug: unique string identifier (e.g., 'catan', 'ticket-to-ride')\ntitle: English or original name\ntitle_ja: Japanese name\nsummary: short Japanese summary\nrules_content: full rules in Markdown or text\nbgg_url: BoardGameGeek URL\nmin_players: minimum number of players\nmax_players: maximum number of players\nplay_time: play time in minutes\nmin_age: minimum age\npublished_year: year published\n"


@tool("schema_search")
def schema_search_tool(query: str) -> str:
    """Search the database for existing game information based on a query string."""
    async def _do_search():
        results = await supabase_repository.search(query)
        return results

    try:
        rows = anyio.run(_do_search)
    except RuntimeError:
        rows = anyio.run(_do_search)
    if not rows:
        return "No results found."
    parts = []
    for i, r in enumerate(rows, 1):
        parts.append(
            f"[{i}] slug={r.get('slug')}\ntitle={r.get('title')} / {r.get('title_ja')}\nsummary={r.get('summary')}\nrules_content={str(r.get('rules_content'))[:500]}...\nurl={r.get('bgg_url')}\n"
        )
    return "\n\n".join(parts)


class ResearchAgentService:
    def __init__(self):
        self.model_name = "gemini/gemini-2.5-flash"
        if not os.getenv("GOOGLE_API_KEY") and os.getenv("GEMINI_API_KEY"):
            os.environ["GOOGLE_API_KEY"] = os.getenv("GEMINI_API_KEY")

    def run_research_task(self, query: str) -> Dict[str, Any]:
        researcher = Agent(
            role="Board Game Researcher",
            goal="Produce accurate and comprehensive board game information in JSON format.",
            backstory="You are an expert board game archivist. You have access to a database of existing games via the schema_search tool. Your job is to research a specific game and produce a final JSON output that matches the database schema. You should verify facts and ensure the Japanese translation is natural.",
            tools=[schema_search_tool],
            verbose=True,
            memory=False,
            llm=self.model_name,
        )
        task = Task(
            description=f"Research the board game '{query}'.\n1. Search for existing information if needed using schema_search.\n2. Compile all details: title, title_ja, summary (Japanese), rules_content (Markdown), min_players, max_players, play_time, min_age, published_year, bgg_url.\n3. Ensure 'summary' is a catchy, accurate Japanese description.\n4. Ensure 'rules_content' is a helpful summary of the rules in Japanese Markdown.\n5. Return the result strictly as a valid JSON object.",
            expected_output="A valid JSON object containing the game fields.",
            agent=researcher,
        )
        crew = Crew(agents=[researcher], tasks=[task], process=Process.sequential)
        result = crew.kickoff()
        try:
            cleaned = str(result).strip()
            if "```json" in cleaned:
                import re

                match = re.search("```json\\s*(.*?)\\s*```", cleaned, re.DOTALL)
                if match:
                    cleaned = match.group(1)
            elif "```" in cleaned:
                match = re.search("```\\s*(.*?)\\s*```", cleaned, re.DOTALL)
                if match:
                    cleaned = match.group(1)
            return json.loads(cleaned)
        except Exception as e:
            print(f"Failed to parse CrewAI result: {e}")
            print(f"Raw result: {result}")
            return {"error": "Failed to generate valid JSON", "raw": str(result)}
