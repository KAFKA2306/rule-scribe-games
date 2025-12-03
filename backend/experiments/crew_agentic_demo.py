"""
backend/experiments/crew_agentic_demo.py

This file is a placeholder for CrewAI and other agentic workflow experiments.
According to the PROJECT_MASTER_GUIDE, all experimental code that uses
multi-agent systems, threads, or complex state management should be placed
in this directory.

These scripts should:
1. Be run locally via `uv run python backend/experiments/crew_agentic_demo.py`
2. Connect directly to Supabase if needed (bypassing the Core API)
3. NOT be imported by the Core application (backend/app)

Example usage (Conceptual):
---------------------------
from crewai import Agent, Task, Crew
from app.services.gemini_client import GeminiClient

# Define Agents
researcher = Agent(
    role='Board Game Researcher',
    goal='Find detailed rules for {game}',
    backstory='...',
    verbose=True
)

# Define Tasks
task1 = Task(
    description='Search for rules of {game}',
    agent=researcher
)

# Instantiate Crew
crew = Crew(
    agents=[researcher],
    tasks=[task1],
    verbose=True
)

# result = crew.kickoff(inputs={'game': 'Catan'})
"""

import os
import sys

# Add backend directory to path so we can import app modules if needed
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))


def main():
    print("This is the designated area for CrewAI experiments.")
    print("Run your experimental agents here.")


if __name__ == "__main__":
    main()
