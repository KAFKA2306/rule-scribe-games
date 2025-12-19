# SEO Strategy & Implementation

This document outlines the Search Engine Optimization (SEO) strategy for **Bodoge no Mikata (ボドゲのミカタ)**. It serves as a living document to track our technical implementation, content strategy, and operational best practices.

## 1. Technical Architecture (The Core)

Our SEO relies on a **Hybrid Rendering** approach to ensure perfect indexability while maintaining a smooth SPA experience (React).

### Server-Side Rendering (SSR) Injection
Since search engine crawlers (especially non-Google ones) can struggle with Client-Side Rendering (CSR), we explicitly handle SEO on the backend.

- **Mechanism**: FastAPI intercepts requests to `/games/{slug}`.
- **Process**:
    1. Fetches game data from Supabase.
    2. Reads the `index.html` template.
    3. **Injects** specific metadata (Title, Description, OGP, JSON-LD) directly into the HTML `<head>`.
    4. Serves the pre-rendered HTML.
- **Key File**: `app/services/seo_renderer.py`

### Canonical URLs
**Critical for preventing duplicate content issues.**
- **Implementation**: Every game page defines a self-referencing canonical tag.
- **Format**: `<link rel="canonical" href="https://bodoge-no-mikata.vercel.app/games/{slug}" />`
- **Result**: Tells Google that this specific URL is the authoritative source for the content, distinguishing it from the homepage.

---

## 2. On-Page Optimization

### Metadata Strategy
| Tag | Pattern | Purpose |
| :--- | :--- | :--- |
| **Title** | `「{Game}」のルールをAIで瞬時に要約 | ボドゲのミカタ` | High CTR, keywords included. |
| **Description** | AI-generated summary + boilerplate pitch. | Unique snippet for SERP. |
| **OG:Image** | Game Cover Art (or default hero). | High engagement on social shares (Twitter/X). |

### Structured Data (JSON-LD)
We implement **Schema.org** vocabulary to help Google understand our content context.
- **Type**: `Game`
- **Properties**:
    - `numberOfPlayers` (QuantitativeValue)
    - `audience` (minAge)
    - `timeRequired` (ISO 8601 Duration)
    - `description` (AI Summary)

---

## 3. Crawling & Indexing

### XML Sitemap
- **Location**: `/sitemap.xml` (Dynamically generated).
- **Handler**: `app/services/sitemap.py`
- **Content**:
    - Static Pages (`/`, `/data`)
    - All Dynamic Game Pages (`/games/{slug}`)
    - `<lastmod>` updated automatically based on DB timestamps.

### Robots.txt
- **Configuration**: Allows all crawlers (`User-agent: *`, `Allow: /`).
- **Sitemap Link**: Explicitly point to the absolute URL of the sitemap.

---

## 4. Operational Strategy (Google Search Console)

### 1. Daily/Weekly Monitoring
- Check **"Coverage"** report for errors (5xx, 4xx).
- Monitor **"Sitemaps"** status to ensure successful fetch.

### 2. Manual Indexing (Speed Strategy)
When adding new games or fixing critical SEO bugs:
1. Go to **URL Inspection**.
2. Enter the specific game URL (e.g., `/games/catan`).
3. Click **"Request Indexing"**.
*Why?* Sitemaps are passive; manual requests are active and prioritized.

### 3. Performance Tracking
- Monitor **CTR (Click-Through Rate)** for keywords "ルール (Rules)", "要約 (Summary)", "インスト (Inst)".
- If impressions are high but CTR is low, optimize the **Title** and **Meta Description** patterns.

---

## 5. Future Optimizations (Backlog)

- [ ] **Breadcrumbs Structured Data**: Add `BreadcrumbList` schema for better SERP hierarchy.
- [ ] **FAQ Schema**: Use `FAQPage` schema for the Rules section (e.g., "How to set up?", "Winning conditions?").
- [ ] **Performance (Core Web Vitals)**: Optimize image loading (Next.js Image or raw `srcset` improvements) to improve LCP (Largest Contentful Paint).
