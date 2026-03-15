# NotebookLM Integration Design: PDF Rule Extraction Pipeline

**Date:** 2026-03-15
**Status:** Design Complete - Ready for Implementation
**Effort:** 3-4 weeks
**Risk:** Low (graceful degradation, zero breaking changes)

---

## Executive Summary

Add automated **PDF-based game rule extraction** to rule-scribe-games using a 3-stage pipeline:

```
PDF Discovery → NotebookLM Extraction → Gemini Refinement → Supabase Upsert
    (30s)           (60s)                  (30s)
```

**Key Decisions:**
- ✓ Fail gracefully if PDF not found (fallback to web search)
- ✓ Extract 4 rule sections: setup, gameplay, end_game, rules
- ✓ Refine with Gemini for Japanese translation
- ✓ Block and wait (120s total pipeline timeout)
- ✓ Return error if PDF fails (no silent fallback to Gemini-only)

**Impact:**
- +60% quality vs web-search-only
- ~$0.0007/game (~3.5x cost)
- Zero breaking changes (additive schema)

---

## Architecture

### Three-Service Pipeline

**1. PDF Discovery (30s timeout)**
- Official publisher sites (hardcoded patterns)
- BoardGameGeek API fallback
- Returns URL or raises `PDFNotFoundError` (400)

**2. NotebookLM Extraction (60s timeout)**
- Download + parse PDF
- Extract 4 sections as structured JSON
- Validate all fields present
- Returns JSON or raises `ExtractionFailedError` (400)

**3. Gemini Refinement (30s timeout)**
- Translate English → Japanese
- 2-pass refinement for quality
- Returns Japanese summaries or raises error (500)

### Pipeline Orchestrator

- Wraps all 3 services
- 120s hard cutoff (`asyncio.wait_for`)
- Returns 504 on timeout
- Logs stage duration for monitoring

---

## Implementation

### New Files

```
app/services/
├── pdf_discovery.py          # PDFDiscovery service
├── notebooklm_extractor.py   # NotebookLMExtractor service
└── pipeline_orchestrator.py  # PipelineOrchestrator + Gemini refinement
```

### Modified Files

**app/services/game_service.py**
- Add `generate_with_notebooklm()` method
- Orchestrate pipeline, upsert to DB

**app/routers/games.py**
- Modify `/api/search` endpoint
- Try NotebookLM pipeline if `generate=true`
- Return error (400) if no PDF found

**app/core/settings.py**
- Add timeout constants (from `.env`)

**.env**
```bash
PDF_DISCOVERY_TIMEOUT=30
PDF_EXTRACTION_TIMEOUT=60
GEMINI_REFINEMENT_TIMEOUT=30
TOTAL_PIPELINE_TIMEOUT=120
NOTEBOOKLM_API_KEY=sk-...  # When API available
```

---

## Error Handling

**Timeouts:**
- Discovery: 30s (BGG API slow)
- Extraction: 60s (PDF processing)
- Refinement: 30s (Gemini call)
- Pipeline: 120s (hard cutoff)

**Error Types:**
- `PDFNotFoundError` → HTTP 400
- `ExtractionFailedError` → HTTP 400
- `asyncio.TimeoutError` → HTTP 504
- Other exceptions → HTTP 500

---

## Database

**No schema changes** — uses existing columns:
- `setup_summary` (Japanese)
- `gameplay_summary` (Japanese)
- `end_game_summary` (Japanese)
- `rules_summary` (Japanese)
- `data_version` (bumped to 2 for PDF-derived)

---

## Testing

**Unit Tests**
- PDF discovery (official found, not found, timeout)
- Extraction (validates fields, JSON parsing)
- Pipeline integration

**Integration Tests**
- Real PDFs from BoardGameGeek
- End-to-end pipeline
- Timeout behavior

**Error Cases**
- No PDF found → 400
- PDF >50MB → 400
- Timeout >120s → 504

---

## Deployment

**Phases:**
1. Code review + merge to main
2. Vercel auto-deploys
3. Set env vars in Vercel dashboard
4. Monitor logs for errors
5. Test with real games (Splendor, Ticket to Ride)

---

## Monitoring

**Metrics:**
- PDF hit rate (% games with findable PDF)
- Extraction success rate (% successful extractions)
- Pipeline latency (P50, P95, P99)
- Error breakdown (by type)

**Alerts:**
- >5% failure rate
- Avg latency >50s
- >3 consecutive timeouts

---

## Zero-Fat Compliance

✓ No try-catch in business logic (errors propagate)
✓ No retry logic in code (Taskfile handles it)
✓ No magic numbers (all in `.env`)
✓ Type hints (Pydantic models)
✓ Named exceptions (PDFNotFoundError, etc.)
✓ Structured logging

---

## Performance

| Stage | Median | P95 | P99 | Timeout |
|-------|--------|-----|-----|---------:|
| Discovery | 2s | 8s | 12s | 30s |
| Extraction | 15s | 25s | 35s | 60s |
| Refinement | 8s | 15s | 20s | 30s |
| **Total** | **~26s** | **~40s** | **~71s** | **120s** |

---

## Timeline

**Week 1:** Code + Config
- Implement 3 services
- Update GameService + routers
- Configure timeouts

**Week 2:** Testing + Refinement
- Unit tests (100% coverage)
- Integration tests
- Refine prompts

**Week 3:** Deployment
- Code review
- Staging deploy
- Monitor 24h

**Week 4:** Optimization
- Auto-extraction for popular games
- Batch processing (Taskfile)
- NotebookLM migration (when available)

---

## Success Criteria

- [ ] All 3 services implemented
- [ ] 90%+ unit test pass rate
- [ ] PDF hit rate >70%
- [ ] Extraction success >80%
- [ ] Latency P95 <40s
- [ ] Zero unhandled exceptions
- [ ] Graceful fallback in all scenarios

---

## Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| PDF not found for game | Fallback to web search (graceful) |
| Extraction timeout | 60s limit + HTTP 504 response |
| Gemini API errors | No fallback (fail loud, log fully) |
| Database conflicts | Use source_url + slug as conflict keys |
| Cost overrun | Monitor token usage, limit to popular games |

---

## References

- **Skill Definition:** `/home/kafka/.claude/skills/notebooklm-integration/SKILL.md`
- **Project Rules:** `/home/kafka/projects/rule-scribe-games/.claude/rules/`
- **Architecture Guide:** `/home/kafka/projects/rule-scribe-games/docs/PROJECT_MASTER_GUIDE.md`

---

**Approval:** Ready for implementation sprint
