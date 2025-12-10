PROMPTS = {
    "metadata_generator": {
        "generate": """
You are an expert board game librarian.
Generate structured JSON metadata for the board game matching the query: "{query}"

Context from database:
{context}

Return ONLY valid JSON with the following keys:
- title: Original title
- title_ja: Japanese title (if available, else same as title)
- summary: A brief 1-sentence summary (Japanese)
- description: A detailed description (Japanese, 3-5 sentences)
- min_players: int
- max_players: int
- play_time: int (minutes)
- age: int (recommended age)
- mechanics: list of strings (e.g. "Deck Building", "Worker Placement")
- tags: list of strings
- rules_content: A structured summary of the rules (in Markdown format, Japanese).
- flavor_text: A short flavor text (Japanese)
- image_prompt: A prompt to generate an image for this game (English)

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
