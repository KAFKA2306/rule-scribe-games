# Project Milestones & Roadmap

This document outlines the development phases, key milestones, and current status of RuleScribe Games.

```mermaid
gantt
    title RuleScribe Games Roadmap
    dateFormat  YYYY-MM-DD
    section Phase 1: Core Foundation
    Project Setup           :done,    des1, 2025-12-01, 2025-12-07
    Database Schema Design  :done,    des2, 2025-12-05, 2025-12-10
    Backend API (FastAPI)   :done,    des3, 2025-12-08, 2025-12-20
    Frontend (React)        :done,    des4, 2025-12-15, 2025-12-25
    AI Generation (Gemini)  :done,    des5, 2025-12-20, 2026-01-05
    Link Resolution Logic   :done,    des6, 2026-01-02, 2026-01-07

    section Phase 2: User Engagement (Current)
    Google Auth Integration :active,  p2_1, 2026-01-10, 2026-01-20
    User Lists (Owned/Wish) :active,  p2_2, 2026-01-15, 2026-01-30
    Likes / Favorites       :         p2_3, 2026-01-25, 2026-02-05
    Enrichment (30 Games)   :active,  p2_4, 2026-01-09, 2026-01-15

    section Phase 3: Social & Community
    Review & Rating System  :         p3_1, 2026-02-01, 2026-02-20
    User Following System   :         p3_2, 2026-02-15, 2026-03-01
    Social Sharing (Lists)  :         p3_3, 2026-02-25, 2026-03-10

    section Phase 4: Advanced AI
    Rule Q&A Chatbot        :         p4_1, 2026-03-01, 2026-03-30
    Personalized Recommend  :         p4_2, 2026-04-01, 2026-04-30
```

## detailed Status

### Phase 1: Core Foundation (Completed)
- **Status**: ✅ Completed
- **Deliverables**:
    - High-speed game search and retrieval.
    - AI-powered game data generation (Japanese rules summary).
    - SEO-optimized game pages.
    - Basic "Zero-Fat" architecture.

### Phase 2: User Engagement (In Progress)
- **Focus**: Transforming from a "search tool" to a "platform" where users can manage their board game life.
- **Current Blocker**: Database Schema Drift (Missing `rules_summary` column) preventing mass enrichment of 30 new games.
- **Next Actions**:
    1.  Fix DB Schema (Add `rules_summary`).
    2.  Run `enrich_new_games.py`.
    3.  Complete Google Auth integration.

### Phase 3: Social & Community (Planned)
- **Focus**: Building a community around board games.
- **Key Features**:
    - User reviews and ratings.
    - Social graph (follower/following).
    - Sharing "Best 10" lists.

### Phase 4: Advanced AI (Future)
- **Focus**: Deepening the AI integration beyond static summaries.
- **Key Features**:
    - Interactive Rule Q&A (handling specific edge cases).
    - Personalized recommendations based on user libraries and ratings.
