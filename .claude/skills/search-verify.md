# Skill: Search and Verify

Research board games and verify site content accuracy.

## When to Use
- User asks about a specific board game
- Need to verify game data accuracy
- Checking if a game exists on the site

## Workflow

### 1. Search for Game Info
```
search_web(query: "[game name] ボードゲーム ルール")
```

Gather:
- Official Japanese title
- Player count, play time, age
- Core mechanics and theme
- Publisher and release year

### 2. Check Database
```sql
SELECT * FROM games WHERE 
  title ILIKE '%[name]%' OR 
  title_ja ILIKE '%[name]%' OR
  slug ILIKE '%[name]%';
```

### 3. Check Production Site
Use browser_subagent to navigate to:
- Search: `https://bodoge-no-mikata.vercel.app/?q=[name]`
- Direct: `https://bodoge-no-mikata.vercel.app/games/[slug]`

### 4. Compare and Report
- Does the game exist in database?
- Is the data accurate vs web search results?
- Are images displaying correctly?
- Is the content in proper Japanese?

## Data Sources
- BoardGameGeek (BGG): International game database
- ボドゲーマ / Bodoge.mafia: Japanese board game community
- JELLY JELLY CAFE: Japanese rules explanations
- Publisher official sites
