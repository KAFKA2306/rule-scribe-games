# Skill: Search and Verify

## Trigger
Check if game exists, verify accuracy.

## Steps

### 1. Web Search
```
search_web(query: "[game] ボードゲーム ルール")
```

### 2. Database Check
```sql
SELECT slug, title_ja, LENGTH(rules_content), bgg_url IS NOT NULL 
FROM games WHERE title_ja ILIKE '%[name]%';
```

### 3. Site Check
browser_subagent → https://bodoge-no-mikata.vercel.app/games/[slug]

### 4. Report
- Exists? Accurate? Links? Rules detailed?
