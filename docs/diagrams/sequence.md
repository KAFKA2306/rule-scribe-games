# Game Data Retrieval & Generation Sequence

This document outlines the core sequence for retrieving and generating board game data in RuleScribe Games.

## Overview

The system prioritizes speed and cost-efficiency by checking the local database (Supabase) first. If a game is not found, or if explicitly requested, it triggers an AI generation process using Gemini 3.0 Flash.

```mermaid
sequenceDiagram
    autonumber
    participant User as User (Browser)
    participant FE as Frontend (React/Vite)
    participant API as Backend (FastAPI)
    participant DB as Supabase (PostgreSQL)
    participant AI as Gemini 3.0 Flash

    Note over User, API: Search Flow

    User->>FE: Enters search query "Catan"
    FE->>API: GET /api/search?q=Catan
    API->>DB: SELECT * FROM games WHERE title ILIKE '%Catan%'
    
    alt Game Found (Cache Hit)
        DB-->>API: Returns Game Record
        API-->>FE: Returns JSON (200 OK)
        FE-->>User: Displays Game List
    else Game Not Found (Cache Miss)
        DB-->>API: Returns Empty List
        API-->>FE: Returns Empty List
        FE-->>User: "No games found. Generate?" prompt
    end

    Note over User, API: Generation Flow

    User->>FE: Clicks "Generate Catan"
    FE->>API: POST /api/search { "query": "Catan", "generate": true }
    
    API->>AI: Generate Game Data (1-shot JSON)
    AI-->>API: Returns Structured JSON
    
    API->>DB: UPSERT Game Data
    DB-->>API: Success
    
    API-->>FE: Returns New Game JSON (201 Created)
    
    FE-->>User: Displays New Game Page

    Note over User, API: Detail View & SEO

    User->>FE: Clicks "Catan"
    FE->>API: GET /api/games/catan
    API->>DB: SELECT * FROM games WHERE slug='catan'
    DB-->>API: Returns Game Record
    API-->>FE: Returns GameDetail JSON
    FE-->>User: Renders Game Details
```

## Key Components

1.  **Frontend (React/Vite)**: Handles user interaction and displays data.
2.  **Backend (FastAPI)**: Orchestrates data retrieval and generation.
3.  **Supabase (PostgreSQL)**: Primary data store and cache.
4.  **Gemini 3.0 Flash**: AI engine for generating game data on-demand.

## Scenarios

### 1. Cache Hit (Fast Path)
- **Trigger**: User searches for an existing game.
- **Flow**: API checks DB -> DB returns data -> API returns data to Frontend.
- **Latency**: < 100ms.
- **Cost**: $0.

### 2. Cache Miss & Generation (Slow Path)
- **Trigger**: User requests generation for a missing game.
- **Flow**: API calls Gemini -> Gemini generates JSON -> API saves to DB -> API returns data.
- **Latency**: 3-5 seconds.
- **Cost**: Gemini API Token usage.


