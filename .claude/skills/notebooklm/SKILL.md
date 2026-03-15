---
name: notebooklm
description: NotebookLM + Gemini pipeline for board game rule extraction and Japanese localization. Extract PDF rulebooks → structure as JSON → translate to Japanese → store in Supabase. Use when ingesting new games or regenerating rule content from source PDFs.
tags: [boardgame, rule-extraction, pdf-parsing, japanese-translation, pipeline]
version: 2.1
---

# NotebookLM Skill: Board Game Rule Extraction Pipeline

Board game rule ingestion via PDF discovery, Playwright extraction, and Gemini Japanese refinement.

## When to Invoke

- **New game ingestion**: "Extract rules from official PDF and create Japanese game record"
- **Rule regeneration**: "Regenerate rules for [game] from source PDF"
- **Batch processing**: "Extract rules for [game list] in parallel"
- **Translation refinement**: "Improve Japanese translation quality for existing rules"

## Current Implementation

### Pipeline Stages

```
1. PDF Discovery (PDFDiscoveryService)
   Find official rulebook URL for game title
   
2. Content Extraction (NotebookLMPlaywrightExtractor)
   Parse PDF → raw rule text as JSON
   Extract: setup, gameplay, winning conditions, components
   
3. Japanese Refinement (Gemini 3.0 Flash)
   Translate extracted rules to Japanese
   Structure as game metadata record
   
4. Database Storage (Supabase)
   Upsert game record with refined rules
   Track data_version for regeneration
```

### Example Workflow

```python
# Extract rules for new game
result = await game_service.generate_with_notebooklm("Wingspan")
# Returns: {
#   "title": "Wingspan",
#   "title_ja": "ウィングスパン",
#   "rules_summary": "...",  # Japanese
#   "setup_summary": "...",  # Japanese
#   "gameplay_summary": "..."  # Japanese
# }
```

## Planned: Infographic Generation

**Status**: Designed but not yet implemented.

When implemented, should add stage after Japanese refinement:

```
3. Infographic Generation
   - Turn flow diagrams (Japanese labels)
   - Component layout visuals
   - Win condition flowcharts
   - Player interaction maps
   
   Styles: professional, instructional, sketch_note, kawaii, etc.
   Output: Store as image_url in Supabase games.image_url
```

Would use Gemini Image Generation or Stable Diffusion with Japanese prompt engineering.

## Rules

- **Japanese First**: All extracted and refined text must be natural, native-level Japanese
- **No Hallucination**: If PDF cannot be found or parsed, fail loudly (don't synthesize rules)
- **Preserve Structure**: Maintain game metadata fields from CLAUDE.md schema
- **One Attempt**: Extract once per game; no retry loops in application code

## Out of Scope

- Manual game creation (non-PDF sources)
- Rule validation or playtesting
- Affiliate link generation (handled by GameService)
- English rule preservation (Japanese-only in rules fields)

## Parallel Execution

Process multiple games concurrently:

```
/fork notebooklm: Extract and refine rules for Wingspan
/fork notebooklm: Extract and refine rules for Istanbul
/fork notebooklm: Extract and refine rules for Splendor
/tasks
```

Use when:
- Ingesting batch of new games
- Regenerating rules for multiple games
- Have multiple PDFs ready

Each fork runs independently; combine results in single batch upsert.

## Integration Points

- **Backend entry**: `POST /api/games/generate` with `notebooklm=true`
- **Service method**: `GameService.generate_with_notebooklm(query)`
- **Pipeline**: `PipelineOrchestrator.process_game_rules(game_title)`
- **Config**: PDF sources in `config/pdf_sources.yaml` (if needed)

## Debugging

- **Missing PDF**: Check `PDFDiscoveryService.find_pdf()` logic
- **Parse errors**: Verify Playwright selector stability in `NotebookLMPlaywrightExtractor`
- **Bad Japanese**: Inspect Gemini prompt in `pipeline_orchestrator.py` refinement step
- **Database errors**: Validate game schema matches `backend/app/models.py`

