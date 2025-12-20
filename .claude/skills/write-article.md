# Skill: Write Outreach Article

## Trigger

User requests writing an article/blog post about a game or generally creating outreach content.

## Project ID

`wazgoplarevypdfbgeau`

## Workflow

### Step 1: Select Game

**If game specified:**
- Find slug: `SELECT slug, title FROM games WHERE title ILIKE '%[name]%';`

**If NO game specified:**
- Find high-potential games:
```sql
SELECT slug, title, view_count 
FROM games 
WHERE view_count > 10 
ORDER BY view_count DESC 
LIMIT 5;
```

### Step 2: Fetch Data for Context

```sql
SELECT title, summary, description, rules_content, structured_data, amazon_url 
FROM games WHERE slug = '[slug]';
```

### Step 3: Draft Article (Note Style)

Create a draft in `articles/note/[NNN]_[slug].md`.
**NNN** should be the next sequential number (check `articles/note/` contents).

**Template:**

```markdown
# Note記事ドラフト：[Game Title]

## タイトル案
1. [Emotional/Impactful Title]
2. [Benefit-driven Title]
3. [Curiosity-driven Title]

---

## 本文

### はじめに
[Hook: 読者の悩みや興味に寄り添う導入]
[このゲームを一言でいうと？]

### どんなゲーム？
[Theme & Objective: 専門用語を使わずに世界観を説明]
[Core Mechanism: やることは「○○して××する」だけ、などシンプルに]

### ここが面白い！3つのポイント

#### 1. [Point 1: Emotional/Tactile]
[コンポーネントの触り心地や、直感的な楽しさ]

#### 2. [Point 2: Strategic/Intellectual]
[悩ましいポイント、成長実感、拡大再生産の快感など]

#### 3. [Point 3: Social/Interaction]
[他プレイヤーとの絡み、駆け引き、盛り上がりどころ]

### 30秒でわかるルール

1. **[Action Set 1]**: [説明]
2. **[Action Set 2]**: [説明]
3. **[Winning Condition]**: [説明]

### もっと詳しく知りたい方へ

「実際に動くルール解説が見たい」
「勝つためのコツ（定石）を知りたい」

そんな方のための、**詳細なルール解説ページ**を用意しました。
スマホで手元に見ながら遊べるように整理してあります。

👉 **『[Game Title]』完全ルールガイド・遊び方マニュアル**
[https://bodoge-no-mikata.vercel.app/games/[slug]](https://bodoge-no-mikata.vercel.app/games/[slug])

---

### おわりに
[締めくくりと推奨アクション]

([Amazon Link via `amazon_url` if available])
```

### Step 4: Archive

- Save the file using `write_to_file`.
- Notify user with a link to the draft for review.

- Save the file using `write_to_file`.
- Notify user with a link to the draft for review.

### Step 5: Post to Note (Chrome)

**Use Chrome to draft the article on Note:**

```
browser_subagent(
  TaskName="Draft Note Article", 
  Task="Navigate to https://note.com/editor. Create a new text note. Type the Title '[Title]'. Copy and paste the content from '[filename]' into the body. Save as draft.", 
  RecordingName="post_note_draft"
)
```

**Note:**
- Ensure the user is logged into Note on the browser environment (or ask them to login).
- If automation fails, provide the copy-text for the user.
