PROMPTS = {
    "metadata_generator": {
        "generate": """
You are an expert board game librarian.
Generate structured JSON metadata for the board game matching the query: "{query}"

Context from database:
{context}

Return ONLY valid JSON matching this schema:
{{
    "title": "Original title",
    "title_ja": "Japanese title (if available, else same as title)",
    "summary": "A brief 1-sentence summary (Japanese)",
    "description": "A detailed description (Japanese, 3-5 sentences)",
    "min_players": int,
    "max_players": int,
    "play_time": int (minutes),
    "min_age": int (recommended age),
    "rules_content": "A structured summary of the rules (in Markdown format, Japanese)",
    "structured_data": {{
        "keywords": [
            {{ "term": "Term (JA)", "description": "Short explanation (JA)" }}
        ],
        "key_elements": [
            {{ "name": "Name (JA)", "type": "Card/Token/Board", "reason": "Why it is crucial" }}
        ],
        "mechanics": ["Deck Building", "Worker Placement"],
        "best_player_count": "e.g. 3-4"
    }}
}}

If the game is not found or unclear, do your best to infer or return generic data for a board game.
"""
    },
    "metadata_critic": {
        "improve": """
Review the following board game metadata:
{content}

Identify any factual errors or missing important details.
Return the improved JSON.
"""
    },
}
