import argparse
import asyncio
import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx
import yaml

try:
    import pytest
except ModuleNotFoundError:
    pytest = None

# Cast to Any to avoid "None" attribute errors in static analysis
pytest_any: Any = pytest


def load_prompt(key: str) -> str:
    path = Path(__file__).resolve().parent.parent / "app" / "prompts" / "prompts.yaml"
    data = yaml.safe_load(open(path, encoding="utf-8"))
    for part in key.split("."):
        data = data[part]
    return str(data).strip()


async def call_gemini(api_key: str, model: str, prompt: str) -> dict[str, Any]:
    url = f"https://generativelanguage.googleapis.com/v1beta/{model}:generateContent"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.1,
            "response_mime_type": "application/json",
        },
    }
    async with httpx.AsyncClient(timeout=300.0) as client:
        resp = await client.post(url, headers={"x-goog-api-key": api_key}, json=payload)
    resp.raise_for_status()
    text = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
    if "```" in text:
        m = re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL)
        if m:
            text = m.group(1)
    m = re.search(r"\{.*\}", text, re.DOTALL)
    return json.loads(m.group(0) if m else text)


if pytest_any:

    @pytest_any.fixture(scope="session")
    def api_key():
        key = os.getenv("GEMINI_API_KEY")
        if not key:
            pytest_any.skip("GEMINI_API_KEY not set; skipping LLM flow integration test")
        return key

    @pytest_any.fixture(scope="session")
    def model():
        return os.getenv("GEMINI_MODEL", "models/gemini-3-flash-preview")

    @pytest_any.fixture(scope="session")
    def query():
        return os.getenv("LLM_FLOW_QUERY", "カタン")

    @pytest_any.fixture(scope="session")
    def output_path():
        path = os.getenv("LLM_FLOW_OUTPUT")
        return path


async def test_llm_flow(api_key: str, model: str, query: str, output_path: str | None):
    record = {
        "timestamp": datetime.now().isoformat(),
        "model": model,
        "query": query,
        "step1_generator": {},
        "step2_critic": {},
        "validation": {},
    }
    print("\n=== LLM Agentic Flow Test (App Integration) ===")
    print(f"Query: {query}, Model: {model}")
    from app.core.settings import settings  # noqa: PLC0415

    settings.gemini_api_key = api_key
    settings.gemini_model = model
    from app.services.game_service import generate_metadata  # noqa: PLC0415

    result = await generate_metadata(query, context="No matches.")
    record["full_output"] = result
    print(f"Output keys: {list(result.keys())}")
    required = ["title", "summary", "rules_content"]
    for f in required:
        _ = result[f]
    record["validation"]["result"] = "PASS"
    print("Validation: PASS")
    if output_path:
        Path(output_path).write_text(json.dumps(record, ensure_ascii=False, indent=2))
        print(f"Results saved to: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Test LLM agentic flow")
    parser.add_argument("--api-key", required=True, help="Gemini API key")
    parser.add_argument("--model", default="models/gemini-3-flash-preview", help="Model name")
    parser.add_argument("--query", default="カタン", help="Game query")
    args = parser.parse_args()
    log_dir = Path(__file__).parent / "logs"
    log_dir.mkdir(exist_ok=True)
    output_path = log_dir / f"{datetime.now().strftime('%Y%m%d%H%M')}.json"
    asyncio.run(test_llm_flow(args.api_key, args.model, args.query, str(output_path)))


if __name__ == "__main__":
    main()
