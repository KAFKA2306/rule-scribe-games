import json
import logging
from typing import Any

from app.core.gemini import GeminiClient
from app.services.infographic_service import InfographicService
from app.services.notebooklm_playwright_extractor import NotebookLMPlaywrightExtractor
from app.services.pdf_discovery import PDFDiscoveryService

logger = logging.getLogger("agents.pipeline_orchestrator")


class PipelineOrchestrator:
    def __init__(self):
        self.discovery = PDFDiscoveryService()
        self.extractor = NotebookLMPlaywrightExtractor()
        self.gemini = GeminiClient()
        self.infographics = InfographicService()

    async def process_game_rules(self, game_title: str, generate_infographics: bool = True) -> dict[str, Any]:
        pdf_url = await self.discovery.find_pdf(game_title)
        if not pdf_url:
            logger.warning(f"No PDF found for {game_title}")
            return {}

        raw_extraction = await self.extractor.extract(pdf_url, "Extract game rules as JSON")

        refinement_prompt = f"""
        Translate and refine these rules to natural Japanese:
        {json.dumps(raw_extraction)}

        Also provide a confidence score (0.0 to 1.0) for each section:
        rules, setup, gameplay, end_game.
        """
        refined = await self.gemini.generate_structured_json(refinement_prompt)

        if generate_infographics:
            try:
                visuals = await self.infographics.generate_with_nano_banana(refined)
                refined.update(visuals)
            except NotImplementedError:
                logger.info(f"Infographics skipped for {game_title}: API not yet available")

        return refined
