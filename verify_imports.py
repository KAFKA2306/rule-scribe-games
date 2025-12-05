import sys
import os

# Add the backend directory to sys.path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

try:
    import crewai
    print("crewai imported successfully")
except ImportError as e:
    print(f"Failed to import crewai: {e}")

try:
    from app.services.research_agent import ResearchAgentService
    print("ResearchAgentService imported successfully")
except ImportError as e:
    print(f"Failed to import ResearchAgentService: {e}")
except Exception as e:
    print(f"Error importing ResearchAgentService: {e}")
