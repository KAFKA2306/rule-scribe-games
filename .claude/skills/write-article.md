# Skill: Write Outreach Article

## Trigger

User requests writing an article/blog post about a game or generally creating outreach content.

## Project ID

`wazgoplarevypdfbgeau`

## Critical Configuration

- **Amazon Affiliate Tag**: `bodogenomikat-22` (Note the spelling!).
    -   *Do NOT use `bodogemikata-22`.*
    -   Ensure `AMAZON_TRACKING_ID` in `.env` matches this.
    -   **Validation**: Always use a specific Product URL when possible, not a search query.

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

### Step 3: Trend Research (Maximizing Access)

**Find the "Now" Angle:**
```text
search_web(query: "[game] 評判 Twitter year:2025")
search_web(query: "[game] 感想 Note")
```
- Identify *why* people are talking about it now.
- Quote a common sentiment or counter it.

### Step 4: Draft Viral Article

Create a draft in `articles/note/[NNN]_[slug].md`.

**Template:**

```markdown
# Note記事ドラフト：[Game Title]

## 🖼 サムネイル作成指示 (Click-Through Booster)
*Agent Note: Use `generate_image` or provide a prompt.*
- **Visual**: [Close-up of components / Emotional reaction shot / Abstract metaphor]
- **Text Overlay**: "[Short Impact Phrase, e.g., '神ゲー確定', '30分で人生変わる']"
- **Color**: Vibrant [Color Code] background.
- **Quota Warning**: Start creation early. If quota fails, check `frontend/public/assets/games` for existing assets.


## 📈 タイトル案 (CTR Focus)
1. **The "Counter-Intuitive"**: [e.g., "Why you should STOP playing Catan and start Splendor"]
2. **The "Specific Number"**: [e.g., "3 reasons why this game conquered the world"]
3. **The "Emotional Payoff"**: [e.g., "I haven't felt this frustrated in 10 years (and I loved it)"]

## 🏷 ハッシュタグ (Search Volume)
#[GameName] #ボードゲーム #アナログゲーム #テーブルゲーム #[RelatedGenre] #[TrendWord]

---

## 本文

### はじめに
[Hook: 最近X(Twitter)で話題の… / 逆に今こそ遊びたい名作…]
[読者の「退屈」や「新しい刺激」への欲求に刺す]

### どんなゲーム？
[30秒でわかる「何をするゲーム？」]
[専門用語禁止。例：「カードを買って、資産を増やす」だけ]

### なぜ今、これが面白いのか？

#### 1. [Trend/Emotional Point]
[ネットでの評判や、実際のプレイでの「脳汁」ポイント]

#### 2. [Mechanic/Strategy Point]
[「あそこでああしていれば…」と布団の中で反省会をしてしまう中毒性]

#### 3. [Replayability/Value Point]
[「もう一回！」が止まらない理由]

### 30秒でわかるルール要約

1. **[Action 1]**
2. **[Action 2]**
3. **[Victory]**

👉 **【ルール完全ガイド】スマホで見れる説明書はこちら**
[https://bodoge-no-mikata.vercel.app/games/[slug]](https://bodoge-no-mikata.vercel.app/games/[slug])

---

### おわりに
[CTA: 今週末の予定は決まりましたか？ / Amazonでポチる前に…]

([Amazon Link via `amazon_url`])
```

## Policy: Truthfulness (Absolute)
- **Never misrepresent the site**: We provide *rules* and *basic tips*, not "pro-level strategy" or "cheats".
- **Zero "Fake News"**: Hooks can be emotional but must be based on real player experiences.
- **Accurate Claims**: Do not promise "life-changing" results unless metaphorical. Focus on the *fun* and *convenience* we actually deliver.

### Step 5: Archive

- Save the file using `write_to_file`.
- Notify user with a link to the draft for review.

### Step 6: Post to Note (Chrome)


**Procedure:**
Note's editor (ProseMirror) resists direct typing. Use JavaScript injection.

**Transformation Rules (Markdown -> Note HTML):**

1.  **Headers (`#`, `##`, `###`)** -> Convert to `<h3>` tags.
    *   *Note only supports one heading level (Large Heading).*
    *   *Example:* `### Title` -> `<h3>Title</h3>`

2.  **Bold (`**text**`)** -> Convert to `<b>` tags.
    *   *Example:* `**Important**` -> `<b>Important</b>`

3.  **Links (Embeds/Umekomi)** -> **DO NOT** use `<a>` tags for embeds.
    *   *Action:* Place the raw URL on its own line in the HTML (e.g., `<p>https://...</p>`).
    *   *Trigger:* After insertion, you **MUST** simulate pressing "Enter" at the end of the URL line.

1.  **Navigate**: `https://note.com/editor`.
2.  **Clear & Insert**:
    -   Use `browser_evaluate` to set `innerHTML` on `.ProseMirror[contenteditable='true']`.
    -   Apply the **Transformation Rules** above to your HTML string.
3.  **Trigger Embeds (Cards)**:
    -   **Generic Links**: Focus end -> Press "Enter".
    -   **Amazon Links (Critical)**: **MUST** use Robust Trigger to avoid plain text failure.
    -   **Robust Trigger Sequence**:
        1.  Focus end of URL.
        2.  Type `Space`.
        3.  Wait 500ms.
        4.  Type `Backspace`.
        5.  Wait 500ms.
        6.  Press `Enter`.
        7.  Wait 15s for card generation.
4.  **Header Image**:
    -   Attempt upload. If flaky/quota fails, **Notify User** to set manually. Do not publish without checking.
5.  **Save**: Click "下書き保存" or "公開へ進む".

```python
# Example JS for insertion (Python string)
html_content = "<h3>Section</h3><p>Text with <b>bold</b>.</p><p>https://example.com</p>"
js_code = f"document.querySelector('.ProseMirror[contenteditable=\"true\"]').innerHTML = `{html_content}`;"
```

#### Definition of Optimal (QC)
- **Headers**: Must be large bold format (<h3>).
- **Bold**: Must be rich text bold (<b>).
- **Links**: Must be **Embedded Cards (Umekomi)**. Plain text URLs are **unacceptable**.

#### Troubleshooting Links (If Embed Fails)
If a link remains plain text after automation:
1.  **Robust Trigger (Auto)**: Try `Space` -> `Wait` -> `Backspace` -> `Wait` -> `Enter` sequence.
2.  **Manual Intervention**: Use `notify_user` to ask the user to manually click the end of the URL and press Enter. This is preferable to publishing a sub-optimal article.

