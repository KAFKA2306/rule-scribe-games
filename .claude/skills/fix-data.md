# Skill: Fix Database Content

Fix data quality issues in the Supabase games table.

## When to Use

- Text displays incorrectly (`\n` as literal text)
- Missing fields (links, metadata)
- User reports content issues

## Database

- Project ID: `wazgoplarevypdfbgeau`
- Table: `games`

## Common Fixes

### Fix Escaped Newlines

```sql
UPDATE games 
SET rules_content = REPLACE(rules_content, '\n', E'\n')
WHERE slug = '[slug]';
```

### Add Missing Links

```sql
UPDATE games SET 
  bgg_url = 'https://boardgamegeek.com/boardgame/[id]',
  amazon_url = 'https://www.amazon.co.jp/s?k=[title_ja]&tag=bodogemikata-22'
WHERE slug = '[slug]';
```

### Expand Short Rules

If rules_content < 500 chars, research and rewrite with full structure:

```sql
UPDATE games SET rules_content = E'## 準備
[detailed setup]

## ゲームの流れ
[turn structure]

## 勝利条件
[win conditions]'
WHERE slug = '[slug]';
```

### Fix Image URL

```sql
UPDATE games 
SET image_url = '/assets/games/[slug].webp'
WHERE slug = '[slug]';
```

## Verification

Use browser_subagent to hard refresh and confirm fix.
