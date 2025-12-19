# Skill: Fix Data

## Trigger
Content issues on game pages (short rules, missing fields, broken text).

## Project ID
`wazgoplarevypdfbgeau`

## Diagnosis
```sql
SELECT slug, title, 
  LENGTH(rules_content) as rules_len,
  amazon_url IS NOT NULL as has_amazon,
  bgg_url IS NOT NULL as has_bgg,
  min_players, max_players
FROM games WHERE slug = '[slug]';
```

## Fixes

### Enrich Rules Content (for first-time players)
```sql
UPDATE games SET rules_content = E'## はじめに\n[概要]\n\n## コンポーネント\n[内容物]\n\n## セットアップ（[X]分）\n[手順]\n\n## ゲームの流れ\n[詳細]\n\n## 勝利条件\n[条件]\n\n## 初心者向けヒント\n[アドバイス]' WHERE slug = '[slug]';
```

### Escaped Newlines
```sql
UPDATE games SET rules_content = REPLACE(rules_content, '\\n', E'\n') WHERE slug = '[slug]';
```

### Missing Amazon Link
```sql
UPDATE games SET amazon_url = 'https://www.amazon.co.jp/s?k=' || title || '&tag=bodogemikata-22' WHERE slug = '[slug]';
```

### Bulk Fill Amazon Links
```sql
UPDATE games SET amazon_url = 'https://www.amazon.co.jp/s?k=' || title || '&tag=bodogemikata-22' WHERE amazon_url IS NULL;
```

### Missing Player Count
```sql
UPDATE games SET min_players = [min], max_players = [max] WHERE slug = '[slug]';
```

### Update structured_data
```sql
UPDATE games SET structured_data = '{"keywords": [...], "key_elements": [...]}'::jsonb WHERE slug = '[slug]';
```

## Batch Diagnosis
```sql
SELECT slug, title, LENGTH(rules_content) as len 
FROM games 
WHERE LENGTH(rules_content) < 500 
ORDER BY len;
```

## Verify
browser_subagent → https://bodoge-no-mikata.vercel.app/games/[slug]
