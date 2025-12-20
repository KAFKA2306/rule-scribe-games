# Skill: Fix Data

## Trigger

Content issues on game pages (short rules, missing fields, broken text).

## Project ID

`wazgoplarevypdfbgeau`

## Quick Diagnosis

```sql
SELECT slug, title, 
  LENGTH(rules_content) as rules_len,
  jsonb_array_length(structured_data->'keywords') as kw_count,
  jsonb_array_length(structured_data->'key_elements') as elem_count,
  amazon_url IS NOT NULL as has_amazon,
  min_players, max_players
FROM games WHERE slug = '[slug]';
```

## Common Fixes

### Enrich Rules Content

```sql
UPDATE games SET rules_content = E'## はじめに\n[概要]\n\n## コンポーネント\n[内容物]\n\n## セットアップ（[X]分）\n[手順]\n\n## ゲームの流れ\n[詳細]\n\n## 勝利条件\n[条件]\n\n## 初心者向けヒント\n[アドバイス]' 
WHERE slug = '[slug]';
```

### Add More Keywords (target: 5-8)

```sql
UPDATE games SET structured_data = jsonb_set(
  structured_data,
  '{keywords}',
  '[{"term": "用語1", "description": "説明"}, {"term": "用語2", "description": "説明"}, ...]'::jsonb
) WHERE slug = '[slug]';
```

### Add More Key Elements (target: 4-6)

```sql
UPDATE games SET structured_data = jsonb_set(
  structured_data,
  '{key_elements}',
  '[{"name": "要素1", "type": "component", "reason": "理由"}, ...]'::jsonb
) WHERE slug = '[slug]';
```

### Fix Escaped Newlines

```sql
UPDATE games SET rules_content = REPLACE(rules_content, '\\n', E'\n') 
WHERE slug = '[slug]';
```

### Fill Missing Amazon Links

```sql
UPDATE games SET amazon_url = 'https://www.amazon.co.jp/s?k=' || title || '&tag=bodogemikata-22' 
WHERE amazon_url IS NULL;
```

### Update Player Count

```sql
UPDATE games SET min_players = [min], max_players = [max] 
WHERE slug = '[slug]';
```

## Batch Diagnostics

### Short Rules (< 500 chars)

```sql
SELECT slug, title, LENGTH(rules_content) as len 
FROM games WHERE LENGTH(rules_content) < 500 ORDER BY len;
```

### Few Keywords (< 5)

```sql
SELECT slug, title, jsonb_array_length(structured_data->'keywords') as kw
FROM games WHERE jsonb_array_length(structured_data->'keywords') < 5;
```

### Missing Images

```sql
SELECT slug, title FROM games WHERE image_url IS NULL;
```

## Verify

```
browser_subagent → https://bodoge-no-mikata.vercel.app/games/[slug]
```
