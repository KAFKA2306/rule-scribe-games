# Skill: Fix Data

## Trigger
Content issues on game pages (broken text, missing fields).

## Project ID
`wazgoplarevypdfbgeau`

## Diagnosis
```sql
SELECT slug, title_ja, 
  LENGTH(rules_content) as rules_len,
  amazon_url IS NOT NULL as has_amazon,
  bgg_url IS NOT NULL as has_bgg
FROM games WHERE slug = '[slug]';
```

## Fixes

### Escaped Newlines
```sql
UPDATE games SET rules_content = REPLACE(rules_content, '\n', E'\n') WHERE slug = '[slug]';
```

### Short Rules (< 500 chars)
```sql
UPDATE games SET rules_content = E'## 準備\n[セットアップ]\n\n## ゲームの流れ\n[ターン構造]\n\n## 勝利条件\n[勝ち方]\n\n## 戦略ヒント\n[アドバイス]' WHERE slug = '[slug]';
```

### Missing Amazon Link
```sql
UPDATE games SET amazon_url = 'https://www.amazon.co.jp/s?k=' || COALESCE(title_ja, title) || '&tag=bodogemikata-22' WHERE slug = '[slug]';
```

### Bulk Fill Amazon Links
```sql
UPDATE games SET amazon_url = 'https://www.amazon.co.jp/s?k=' || COALESCE(title_ja, title) || '&tag=bodogemikata-22' WHERE amazon_url IS NULL;
```

### Missing BGG Link
```sql
UPDATE games SET bgg_url = 'https://boardgamegeek.com/boardgame/[id]' WHERE slug = '[slug]';
```

### Update structured_data
```sql
UPDATE games SET structured_data = '{"keywords": [...], "key_elements": [...]}'::jsonb WHERE slug = '[slug]';
```

## Verify
browser_subagent → https://bodoge-no-mikata.vercel.app/games/[slug] → Ctrl+Shift+R
