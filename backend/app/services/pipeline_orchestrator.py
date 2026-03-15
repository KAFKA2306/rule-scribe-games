import json
import logging
from typing import Any

from app.services.notebooklm_playwright_extractor import NotebookLMPlaywrightExtractor
from app.services.pdf_discovery import PDFDiscoveryService

from app.core.gemini import GeminiClient

logger = logging.getLogger("agents.pipeline_orchestrator")


class PipelineOrchestrator:
    def __init__(self):
        self.discovery = PDFDiscoveryService()
        self.extractor = NotebookLMPlaywrightExtractor()
        self.gemini = GeminiClient()

    async def process_game_rules(self, game_title: str) -> dict[str, Any]:
        pdf_url = await self.discovery.find_pdf(game_title)
        raw_extraction = await self.extractor.extract(pdf_url, "Extract game rules as JSON")

        refinement_prompt = f"Translate and refine these rules to Japanese: {json.dumps(raw_extraction)}"
        refined = await self.gemini.generate_structured_json(refinement_prompt)

        return refined
