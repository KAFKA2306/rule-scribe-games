# System Diagrams

## Search & Metadata Generation Flow

This diagram illustrates the flow of a user search request, specifically focusing on the interaction between the Frontend, Backend, and Gemini API, including the "Crash Only" behavior when limits are hit.

```mermaid
sequenceDiagram
    participant User
    participant FE as Frontend App.jsx
    participant API as Vercel API main.py
    participant DB as Supabase
    participant AI as Gemini API

    User->>FE: Enters specific game name e.g., "Catan"
    FE->>API: POST /api/search query="Catan", generate=true
    activate API
    
    API->>DB: Search existing games
    DB-->>API: Return matches or empty
    
    rect rgb(255, 240, 240)
        note right of API: Metadata Generation CRASH ONLY MODE
        API->>AI: generate_metadata query
        activate AI
        
        alt Success Process < 8s
            AI-->>API: JSON Response Title, Summary, Rules
            deactivate AI
            API->>DB: Upsert Game Data
            DB-->>API: Success
            API-->>FE: Return Game List
            FE-->>User: Display Game Cards
        else Failure: 503 Service Unavailable REAL
            activate AI
            AI--xAPI: 503 Service Unavailable
            deactivate AI
            note right of API: NO FALLBACK / NO RETRY
            API--xFE: 500 Internal Server Error Raw Stack Trace
            FE--xUser: Error Banner No recovery
        else Failure: Timeout Vercel Limit > 10s DANGER
            activate AI
            AI-->>API: Processing... >10.0s
            deactivate AI
            note right of API: Vercel HARD TIMEOUT Process Killed
            API--xFE: 504 Gateway Timeout or Connection Reset
            FE--xUser: INFINITE LOADING Hang - No finally block
        end
    end
    deactivate API
```

## Component Architecture

```mermaid
graph TD
    User[User Browser]
    
    subgraph Frontend [React Frontend]
        App[App.jsx]
        Search[Search Form]
        Grid[Game Grid]
        API_Lib[lib/api.js]
    end
    
    subgraph Backend [FastAPI / Python]
        Main[main.py]
        Service[game_service.py]
        GeminiClient[core/gemini.py]
    end
    
    Ext_AI[Google Gemini API]
    Ext_DB[Supabase PostgreSQL]

    User --> Search
    Search --> App
    App --> API_Lib
    API_Lib -->|HTTP Request| Main
    
    Main --> Service
    Service -->|Read/Write| Ext_DB
    Service -->|Generate Content| GeminiClient
    GeminiClient -->|REST API| Ext_AI
```
