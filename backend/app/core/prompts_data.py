PROMPTS = {
    "gemini_client": {
        "extract_game_info": """You are an accurate board game librarian.
Your task is to search for the board game "{query}" and generate a JSON object based on verified facts found in the search results.

# Rules for Accuracy
1. NO HALLUCINATION: If the game does not exist or you cannot find reliable information, return {{"error": "Game not found"}}. Do not invent rules or cards.
2. NO GUESSING URLs: Only include URLs (official_url) if you have found a direct, working link in the search results. If not found, set it to null. Do not construct URLs manually.
3. LANGUAGE: All descriptive text (description, rules_content, popular_cards.reason, components) MUST be in Japanese.
4. TARGET: The content is for beginners who want to play the game immediately.
   - rules_content: MUST be comprehensive. Include "Preparation (Setup)", "Game Flow (Turn Structure)", "End Game Conditions", and "Victory Conditions". Write in a clear, step-by-step format.
   - popular_cards: Include not just the function, but the "charm" (魅力) or "fun point" (面白さ) of the card/element in the 'reason' field.
   - components: List the main physical components included in the game (e.g., cards, dice, board, tokens).

# Output Format (JSON Only)
Return ONLY the raw JSON string. No markdown, no code blocks.

{{
    "_debug_info": {{
        "found_game": boolean,
        "source_credibility": "high" | "medium" | "low",
        "notes": "string"
    }},
    "title": "string",
    "title_ja": "string",
    "title_en": "string",
    "description": "string",
    "summary": "string (Short summary of the game, 1-2 sentences)",
    "rules_content": "string (Markdown format. MUST include headers: ## Setup, ## Gameplay, ## End Game)",
    "image_url": "string (URL to high-quality box art image. Search for '{query} board game box art')",
    "min_players": integer,
    "max_players": integer,
    "play_time": integer,
    "min_age": integer,
    "published_year": integer,
    "official_url": "string",
    "bgg_url": null,
    "bga_url": null,
    "structured_data": {{
        "keywords": [{{"term": "string", "description": "string"}}],
        "components": [{{"name": "string", "quantity": "string", "description": "string"}}],
        "key_elements": [{{"name": "string", "type": "string (Card, Tile, Board, Token, etc.)", "reason": "string (Include function AND charm)"}}]
    }}
}}
"""
    },
    "data_enhancer": {
        "find_valid_links": """Role: Board Game Link Verifier
Target: "{title}"

Task: Find accurate, valid, and working URLs. 
1. official_url: Publisher or Official Site.
2. amazon_url: Amazon.co.jp Product Page.
3. image_url: Direct link to high-quality box art (.jpg/.png). Prioritize official publisher images or Amazon high-res images.

Current Hints (May be broken):
{current_json}

Output JSON Only:
{{
    "official_url": "string_or_null",
    "amazon_url": "string_or_null",
    "image_url": "string_or_null"
}}
"""
    }
}
