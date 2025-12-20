# Skill: Write Outreach Article

## Config
- Project ID: `wazgoplarevypdfbgeau`
- Amazon Tag: `bodogenomikat-22`
- Site: `https://rule-scribe-games.vercel.app`
- Note Account: `https://note.com/bodogenomikata`

## Workflow

### 1. Select Games
Query DB for high view_count games.

### 2. Draft Article
Save to `articles/note/[NNN]_[theme].md`

Structure:
- Title
- Hashtags
- Intro (personal, casual)
- Ranking (3rd → 2nd → 1st)
- Each game: description + rule link + Amazon link
- Closing

### 3. Convert & Post
- Convert markdown to HTML `<p>` tags
- Navigate to `https://note.com/notes/new`
- Inject HTML via JS to `.ProseMirror[contenteditable="true"]`

### 4. Embed Links
For each URL: `Space → Wait → Backspace → Wait → Enter → Wait`

### 5. Save Draft
Click save button.

## Writing Rules
- Friendly tone (ですます調)
- No aggressive words
- All links must be embedded cards
