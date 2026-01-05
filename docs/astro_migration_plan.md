# Astro Migration Plan & Research Report

## Executive Summary
Migrating "Bodoge no Mikata" (Board Game Ally) from a **Vite React SPA + Python SSR Injection** architecture to **Astro** is highly recommended. The current architecture suffers from complexity (string-replacing HTML in Python for SEO) and performance overhead (Lambda cold starts for content pages). 

Astro will simplify the stack into a unified **Static Site Generation (SSG)** or **Server-Side Rendering (SSR)** model, where game pages are pre-rendered for instant load times and perfect SEO, while retaining React for interactive elements (Search, Filters).

## 1. Current Architecture Analysis
The current application uses a hybrid approach:
-   **Frontend**: Vite + React SPA. The `App.jsx` handles client-side routing and fetches all games (limit=1000) on load.
-   **Backend (Python)**: `api/index.py` (FastAPI) handles API requests (`/api/*`) AND serves game pages (`/games/:slug`).
-   **SEO/SSR mechanism**: The Python backend reads the built `index.html`, performs string replacement to inject `<title>`, `<meta>`, and Schema.org JSON-LD, and even injects a static HTML preview into `<div id="root">`.

**Issues**:
-   **Fragility**: SEO relies on string replacement in `index.html`. If the build output changes, SEO breaks.
-   **Complexity**: Two routing systems (React Router vs FastAPI routing).
-   **Performance**: The Python function must run for every page visit to serve HTML, incurring cold start latency.

## 2. Proposed Architecture (Astro)
Astro allows you to build a content-focused website (perfect for rule explanations) with "Islands" of interactivity.

-   **Routing**: Handled by Astro's file-based routing (`src/pages`).
-   **Rendering**:
    -   **List Page (`/`)**: Static or Server-rendered.
    -   **Game Page (`/games/[slug]`)**: pre-rendered (SSG) for max performance and SEO.
-   **Interactivity**: React components (`ThinkingMeeple`, `SearchForm`) are mounted as Islands (`client:load`) where needed.
-   **Data Fetching**: 
    -   **Build Time**: Astro fetches games from Supabase directly during build to generate static pages.
    -   **Runtime**: Client-side React islands can still fetch from `/api` for dynamic search or generation.
-   **Backend**: The `api/` folder remains only for dynamic API endpoints (Search, AI Generation). The SEO logic in Python is deleted.

## 3. Migration Roadmap

### Phase 1: Application Setup
1.  Initialize Astro with React support.
2.  Port `frontend/src/index.css` to Astro global styles.
3.  Move shared UI components (`ThinkingMeeple`, `GameBackground`) to `src/components`.

### Phase 2: Page Migration
1.  **Index Page (`src/pages/index.astro`)**:
    -   Fetch initial game list from Supabase (server-side).
    -   Render the Layout and the React `App` (or a refactored `GameList` component) as an Island.
    -   *Simplicity Note*: To keep the "Split Pane" app-feel, we can keep the main UI as a React Island, but serve it from Astro.
    
2.  **Detail Page (`src/pages/games/[slug].astro`)**:
    -   Use `getStaticPaths` to fetch all game slugs from Supabase.
    -   Fetch game details.
    -   Render proper `<head>` metadata (Title, Description, OGP, JSON-LD) using Astro components. **No more Python injection.**
    -   Render the game content (Rules, Summary).

### Phase 3: Cleanup & Routing
1.  Update `vercel.json` to route `/games/*` to the Astro build output instead of `api/index.py`.
2.  Delete `app/services/seo_renderer.py` and the `/games/{slug}` route in `app/main.py`.

## 4. Key Implementation Details

### Supabase Integration
Astro runs server-side (node/bun/deno during build), so we can use `supabase-js` directly.
```javascript
// src/lib/supabase.js
import { createClient } from '@supabase/supabase-js';
export const supabase = createClient(
  import.meta.env.PUBLIC_SUPABASE_URL,
  import.meta.env.PUBLIC_SUPABASE_ANON_KEY
);
```

### View Transitions
To maintain the "App-like" feel (smooth transitions between list and detail), Astro's **View Transitions** (`<ViewTransitions />`) can be used. This allows the persistent "Shell" (Header, List potentially) to stay while the content changes, simulating an SPA.

## 5. Decision: Simplicity vs "App" Feel
-   **Simplicity Path (Recommended)**: Standard Website structure. `index.astro` lists games. Clicking one goes to `games/[slug]`. Browser navigation is fast.
-   **App Path**: Keep the "Split Pane" sticky sidebar. This requires either `ViewTransitions` with persistent islands OR keeping the specific "Master-Detail" React component on the Client.
    -   *Recommendation*: Given the user wants a "Simple Page", the Standard Website structure is usually better for mobile/SEO, but we can style the desktop view to look like a split pane using CSS Grid Layouts that persist via View Transitions.
