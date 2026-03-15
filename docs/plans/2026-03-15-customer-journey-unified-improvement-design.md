# RuleScribe v2: Customer Journey Unified Improvement Design

**Date**: 2026-03-15  
**Status**: Approved  
**Scope**: Frontend display, backend stability, content accuracy, infographic generation, smart pipeline

---

## Executive Summary

This spec defines a holistic improvement to RuleScribe Games across five architectural layers, organized through the customer journey: **Search → Generate/Browse → View Detail → Engage**. The goal is to realize the "Transparent Game Library" vision: users discover games through fast, accurate search, instantly see verified rules and data, and visual infographics explain complex mechanics with full explainability.

---

## North Star: "The Transparent Game Library"

**Vision**: Users discover games through fast, accurate search → instantly see verified rules and data → visual infographics explain complex mechanics → system transparently shows *why* information is trustworthy

**Guiding Principles**:
1. **Speed** - Zero friction from search to understanding
2. **Accuracy** - Content is verified, sourced, and traceable
3. **Clarity** - Infographics and visuals explain rather than decorate
4. **Reliability** - Backend never crashes; pipeline never silently fails
5. **Explainability** - Users know the source and confidence level of every fact

---

## Five Improvement Layers

### Layer 1: Frontend Display
**Goal**: Fast, intuitive discovery and immersive detail view

**Requirements**:
- Search is instant (type-ahead, no lag)
- Game cards preview key info (player count, complexity, theme)
- Detail view (GamePage) loads in <1s with tabs for Rules/Infographics/Data
- Responsive design (mobile, tablet, desktop parity)
- Accessibility: WCAG 2.1 AA standard

### Layer 2: Backend Stability
**Goal**: Zero crashes, predictable latency, graceful degradation

**Requirements**:
- API endpoints return <200ms for search, <500ms for generation
- Error handling is explicit: never silent failures, always actionable messages
- Request validation prevents garbage data upstream
- Async tasks (generation) report status clearly (pending/success/failed)
- Rate limiting and queue management for Gemini/Supabase calls

### Layer 3: Content Accuracy
**Goal**: Verified, sourced, traceable game information

**Requirements**:
- Rules summaries are fact-checked against source PDFs
- Japanese translations maintain accuracy (not just machine translation)
- Source URLs are verified as active and correct
- Data versioning tracks what changed and why
- Confidence scores on extracted facts (high/medium/low)

### Layer 4: Infographic Generation
**Goal**: Visual explanations that make complex rules intuitive

**Requirements**:
- Auto-generate diagrams for game setup, turn structure, winning conditions
- Infographics are schema-based (not just pretty images without meaning)
- Explainability: users see *which rule* is visualized and *why*
- Multi-language support (English + Japanese on same graphic)

### Layer 5: Smart Pipeline
**Goal**: Intelligent orchestration from PDF → structured data → user view

**Requirements**:
- PDF extraction detects rule blocks, game phases, player actions
- Gemini calls are optimized (fewer tokens, better prompting)
- Content flows through a quality gate: extract → validate → enrich → publish
- Regeneration is intelligent: only update changed sections, not the whole record
- Logging at each stage enables debugging without guessing

---

## Customer Journey Integration

### Stage 1: Search
**User Goal**: Find a game quickly  
**Layers Involved**: Frontend, Backend, Content, Pipeline

- *Frontend*: Type-ahead, instant results, card previews
- *Backend*: <200ms response, smart filtering
- *Content*: Verified game titles/descriptions indexed for search
- *Pipeline*: Games properly categorized and tagged for discovery

**Success Metrics**:
- Search latency: <200ms (p95)
- Mobile responsiveness: passes lighthouse audit (85+)

### Stage 2: Generate/Browse
**User Goal**: Get or refine game information  
**Layers Involved**: Frontend, Backend, Content, Infographics, Pipeline

- *Frontend*: "Generate" button, loading states, progress indicators
- *Backend*: Async queue management, graceful timeout handling
- *Content*: Generation creates verified rules/summaries
- *Infographics*: Initial schema created during generation
- *Pipeline*: Gemini calls optimized, validation gates enforced

**Success Metrics**:
- Generation latency: <30s (p95)
- Generation success rate: >98%

### Stage 3: View Detail (GamePage)
**User Goal**: Understand the game's rules and mechanics  
**Layers Involved**: Frontend, Backend, Content, Infographics, Pipeline

- *Frontend*: Tabs (Rules/Infographics/Data) load in <1s, responsive
- *Backend*: Fetch complete game record with confidence metadata
- *Content*: Display source URLs, confidence scores, version history
- *Infographics*: Render visual explanations with interactive elements
- *Pipeline*: Data versioning shows what changed and when

**Success Metrics**:
- Detail page load: <1s (p95)
- Rule accuracy: 95%+ match to source PDF
- Infographic clarity: users understand game setup from visual alone

### Stage 4: Engage & Trust
**User Goal**: Save, share, and deepen understanding  
**Layers Involved**: Frontend, Content, Infographics, Backend, Pipeline

- *Frontend*: Share buttons, bookmark, feedback mechanism
- *Content*: Show source attribution, fact-checking notes
- *Infographics*: "Why this rule is visualized this way" explainability
- *Backend*: Support user feedback → regeneration loop
- *Pipeline*: Feedback triggers intelligent re-extraction

**Success Metrics**:
- Time-on-page increases 15%+ for pages with infographics
- Game detail views increase 20%+ (month-over-month)

---

## Success Criteria (All Dimensions)

### Performance
- Search latency: <200ms (p95)
- Detail page load: <1s (p95)
- Generation completion: <30s (p95)
- Zero unhandled errors in production

### Content Quality
- Rule accuracy: 95%+ match to source PDF (spot-check 10 games/quarter)
- Japanese translation quality: native speaker review scores ≥4/5
- Source URL verification: 100% active links at publish time
- Confidence metadata: all facts tagged with confidence level

### User Experience
- Mobile responsiveness: passes lighthouse audit (85+)
- Accessibility: WCAG 2.1 AA compliant
- Infographic clarity: users understand game setup from visual alone (A/B test)

### System Reliability
- API uptime: 99.9% (no cascading failures from Gemini/Supabase timeouts)
- Regeneration success rate: >98% (failed jobs are logged and retryable)
- Pipeline transparency: every failure shows root cause in logs

### Engagement
- Game detail views increase 20%+ (month-over-month)
- Time-on-page increases 15%+ for pages with infographics

---

## Architecture Constraints & Dependencies

1. **Supabase**: Must support data versioning, soft deletes, and confidence metadata
2. **Gemini API**: Rate-limited; requires queue management and fallback handling
3. **Frontend**: Must support dynamic infographic rendering (SVG/Canvas)
4. **PDF Processing**: Requires schema detection before Gemini ingestion

---

## Next Steps

1. Implementation planning (invoke writing-plans skill)
2. Prioritize layers by impact (recommend: Backend Stability → Content Accuracy → Infographics → Frontend → Pipeline)
3. Assign teams to each layer
4. Validate success metrics are measurable and achievable

---

**Approved by**: User  
**Design Review**: Complete  
**Ready for Implementation Planning**: Yes
