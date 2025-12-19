# Skill: Fix Data

## Trigger
Content issues on game pages (broken text, missing fields).

## Project
`wazgoplarevypdfbgeau`

## Common Fixes

### Escaped Newlines
```sql
UPDATE games SET rules_content = REPLACE(rules_content, '\n', E'\n') WHERE slug = '[slug]';
```

### Short Rules (< 500 chars)
Re-research and expand:
```sql
UPDATE games SET rules_content = E'## 準備\n...\n\n## ゲームの流れ\n...' WHERE slug = '[slug]';
```

### Missing Links
```sql
UPDATE games SET 
  bgg_url = 'https://boardgamegeek.com/boardgame/[id]',
  amazon_url = 'https://www.amazon.co.jp/s?k=[title_ja]&tag=bodogemikata-22'
WHERE slug = '[slug]';
```

### Update structured_data
```sql
UPDATE games SET structured_data = '{
  "keywords": [...],
  "key_elements": [...]
}'::jsonb WHERE slug = '[slug]';
```

## Verify
browser_subagent → Ctrl+Shift+R → confirm fix
