# Skill: Search and Verify

Research board games and verify site content.

## When to Use

- Verify game data accuracy
- Check if game exists on site
- Research before adding

## Workflow

### 1. Search

```
search_web(query: "[game name] ボードゲーム ルール")
```

Gather: title, theme, player count, mechanics, BGG ID

### 2. Check Database

```sql
SELECT slug, title_ja, LENGTH(rules_content) as rules_len,
  bgg_url IS NOT NULL as has_bgg
FROM games 
WHERE title ILIKE '%[name]%' OR title_ja ILIKE '%[name]%';
```

### 3. Check Site

```
browser_subagent: https://bodoge-no-mikata.vercel.app/games/[slug]
```

### 4. Report

- Exists? Data accurate? Links present? Rules detailed?

## Data Sources

- BoardGameGeek (BGG)
- ボドゲーマ
- JELLY JELLY CAFE
