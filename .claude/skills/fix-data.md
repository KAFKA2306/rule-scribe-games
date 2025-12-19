# Skill: Fix Database Content

Diagnose and fix data quality issues in the Supabase games table.

## When to Use
- Text displays incorrectly (escaped characters like `\n` showing as literal text)
- Missing fields or broken formatting
- User reports content issues on the site

## Database Reference
- Project ID: `wazgoplarevypdfbgeau`
- Table: `games`
- Key columns: `slug`, `title`, `title_ja`, `summary`, `description`, `rules_content`, `structured_data`, `image_url`

## Common Fixes

### Fix Escaped Newlines
When `\n` appears as literal text instead of line breaks:
```sql
UPDATE games 
SET rules_content = REPLACE(rules_content, '\n', E'\n')
WHERE slug = '[slug]';
```

### Fix Missing Image URL
```sql
UPDATE games 
SET image_url = '/assets/games/[slug].webp'
WHERE slug = '[slug]' AND image_url IS NULL;
```

### Verify Data
```sql
SELECT slug, title_ja, 
       LEFT(rules_content, 100) as rules_preview,
       image_url
FROM games 
WHERE slug = '[slug]';
```

### Update Structured Data
```sql
UPDATE games 
SET structured_data = '{
  "keywords": [
    {"term": "[keyword]", "description": "[desc]"}
  ],
  "key_elements": [
    {"name": "[name]", "type": "[type]", "reason": "[reason]"}
  ]
}'::jsonb
WHERE slug = '[slug]';
```

## Verification
After fix, use browser_subagent to hard refresh the game page and confirm the content displays correctly.

## Prevention
- Always use actual newlines in SQL INSERT statements, not escaped `\n`
- Test content locally before bulk inserts
- Use `E'...'` escape syntax in PostgreSQL for special characters
