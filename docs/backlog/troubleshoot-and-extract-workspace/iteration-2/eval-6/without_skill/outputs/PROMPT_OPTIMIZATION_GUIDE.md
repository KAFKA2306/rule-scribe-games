# Gemini Prompt Optimization: Content Quality & Validation

## Executive Summary

Current prompt architecture produces **valid JSON** but **inconsistent content quality** due to:
1. Vague output expectations (e.g., "simple" vs "detailed")
2. No structured validation hooks
3. Insufficient constraint enforcement in prompt design
4. Missing feedback loops for quality assessment

This guide provides **prompt engineering techniques**, **validation rules**, and **optimization examples** to improve consistency.

---

## Part 1: Current State Analysis

### 1.1 Identified Problems

**Problem 1: Ambiguous Output Length**
```
Current: "A detailed description in Japanese (3-5 sentences)"
Issue:   LLM interprets "detailed" inconsistently
Result:  Some games get 2-line summaries; others get 10-line essays
```

**Problem 2: Jargon Escape Hatches**
```
Current: "Avoid Katakana jargon where possible"
Issue:   "where possible" is not a constraint, it's a suggestion
Result:  Games with technical mechanics (e.g., "ワーカープレイスメント") get unexplained jargon
```

**Problem 3: Missing Specificity in Examples**
```
Current: "keywords: Include 5-8 important game terms"
Issue:   No example of what "5-8 terms" looks like
Result:  Keywords list varies: 3 terms, 12 terms, or missing entirely
```

**Problem 4: No Consistency Check Phase**
```
Current: One-pass generation → Upsert
Issue:   No self-review or consistency validation
Result:  Rules content can contradict metadata; keywords not aligned with body text
```

**Problem 5: Temperature = 0 but Structure Varies**
```
Current: temperature: 0 (deterministic), but prompt is soft-constrained
Issue:   Even at T=0, soft constraints allow variance
Result:  Same input produces different output structures across runs
```

---

## Part 2: Prompt Engineering Improvements

### 2.1 Technique 1: Hard Constraints via Counting

**Before (Soft)**:
```
"keywords: Include 5-8 important game terms"
```

**After (Hard)**:
```
"keywords: EXACTLY 6 terms (no more, no less). Format:
[
  { "term": "用語名 (JA)", "description": "説明 (JA)" },
  { "term": "用語名 (JA)", "description": "説明 (JA)" },
  ...6 total...
]"
```

**Why it works**: 
- LLM counts to ensure compliance
- JSON structure validation catches violations
- If LLM returns 5 or 7 terms, Pydantic validator rejects it

---

### 2.2 Technique 2: Exemplar-Driven Constraints

**Before (Vague)**:
```
"description: A detailed description in Japanese (3-5 sentences)"
```

**After (Exemplar)**:
```
"description: Japanese description, EXACTLY 3-5 sentences. Must include:
1. What is the core experience? (1 sentence)
2. What will I be doing? (1-2 sentences)
3. Why would I enjoy this? (1 sentence)

EXAMPLE for Catan:
「カタンは、島を開拓するボードゲームです。砂漠の島にあなたの入植地を建設し、資源を集めて町や都市を発展させます。友達と競争しながら、最初に10勝利点を獲得したプレイヤーが島を支配できる最高の瞬間を体験できます。」

Your output:"
```

**Why it works**:
- Example sets length and structure expectations
- LLM mirrors format without deviation
- Easier to validate (sentence count, structure presence)

---

### 2.3 Technique 3: Inline Validation Schema

**Before (Post-Validation)**:
```
// Response validation happens AFTER Gemini returns
// If validation fails, error is logged but no correction attempted
```

**After (Embedded)**:
```
"Return JSON matching this EXACT schema with these rules:
{
  'title': string (max 100 chars, no jargon),
  'summary': string (EXACTLY 1 sentence, 50-80 chars, Japanese only),
  'rules_content': markdown string with structure:
    - Section 1: [ゲームの概要と魅力 2-3文]
    - Section 2: [内容物リスト]
    - Section 3: [準備手順 numbered 1-5]
    - Section 4: [詳細な手順説明 numbered 1-X]
    - Section 5: [終了条件と勝者の決め方]
    - Section 6: [戦略アドバイス 3つ]
  'keywords': array of EXACTLY 6 objects with structure:
    { 'term': string (max 20 chars), 'description': string (50-100 chars) }
  'key_elements': array of EXACTLY 5 objects
  'mechanics': array of 3-6 strings
}

VALIDATION RULES:
- rules_content must contain all 6 sections
- keywords descriptions must be plain language (no jargon)
- key_elements reasons must answer: 'Why would a player enjoy this?'
- summary must be single sentence ending with period"
```

**Why it works**:
- Constraint is part of prompt, not post-processing
- LLM validates as it generates
- Structure violations cause Gemini to self-correct

---

### 2.4 Technique 4: Adversarial Examples (What NOT to Do)

**Before (No negative examples)**:
```
"Avoid jargon"
```

**After (With bad examples)**:
```
"Do NOT output these types of descriptions:
❌ ゲームのメカニクスはワーカープレイスメントとドラフティングの組み合わせで、...
❌ このゲームはリソースマネジメントがコアのエンジンですね。
❌ 要約：プレイヤーが交渉を通じてネットワークを構築します。

✅ こうしてください：
✅ ゲームの基本：プレイヤーが労働者を配置して、資源を集めます。
✅ 楽しさ：友達と一緒に町を育てることができます。
✅ 説明：参加者が相談して、路線を作ります。"
```

**Why it works**:
- Negative examples teach boundary detection
- LLM learns what violates constraints
- Error rate drops on similar games

---

### 2.5 Technique 5: Chain-of-Thought Enforcement

**Before (Direct output)**:
```
"Return ONLY valid JSON"
```

**After (CoT with JSON extraction)**:
```
"Process in order:
1. [ANALYSIS] Identify core mechanics, target players, key fun factors
2. [DRAFT] Write rules_content with all 6 sections in Japanese
3. [KEYWORDS] Extract 6 gameplay-relevant terms with plain-language explanations
4. [VALIDATE] Check that:
   - Each keyword appears in rules_content
   - No two keywords describe the same concept
   - All jargon has plain-language alternative
5. [OUTPUT] Return JSON

Format your thinking as:
[ANALYSIS]
Mechanics: ...
Target Players: ...
Fun Factors: ...

[DRAFT]
[ゲームの概要...]

[KEYWORDS]
1. 用語: ...

[VALIDATE]
Keyword 1 appears in rules_content? Yes/No - Why?

[OUTPUT]
{ ... JSON ... }"
```

**Why it works**:
- Multi-step process forces deliberate choices
- Internal validation catches errors before JSON output
- Transparency helps debug failures

---

### 2.6 Technique 6: Confidence Scoring & Fallback

**Before (No confidence signal)**:
```
// If context is weak, Gemini still outputs with equal confidence
```

**After (Confidence-aware)**:
```
"If you are UNCERTAIN about any field, add a confidence score:
{
  'title': 'Game Name',
  'title_confidence': 0.95,  // 1.0 = verified, 0.5 = inferred, 0 = hallucinated
  'summary': 'Description',
  'summary_confidence': 0.7,
  'rules_content': '...',
  'rules_confidence': 0.3,  // Low confidence if rules not verified
  'source_used': 'Web search | Training data | Inference from similar games'
}

RULES:
- confidence >= 0.8: Safe to display
- confidence 0.5-0.8: Mark with [⚠️ AI-generated, may be incomplete]
- confidence < 0.5: Omit field, prompt user to add manual content"
```

**Why it works**:
- Transparency to end-users
- Backend can filter unreliable content
- Humans know when to verify

---

## Part 3: Validation Rules & Implementation

### 3.1 Structure Validation (Pydantic)

**Current validation** (app/models.py):
```python
class GeneratedGameMetadata(BaseSchema):
    title: str
    summary: str
    rules_content: str
    structured_data: StructuredData
    # ↑ Accepts any rules_content string
```

**Improved validation**:
```python
from pydantic import field_validator, Field
import re

class GeneratedGameMetadata(BaseSchema):
    title: str = Field(..., max_length=100)
    summary: str = Field(..., min_length=30, max_length=150)
    
    @field_validator('summary')
    @classmethod
    def validate_summary_is_single_sentence(cls, v: str) -> str:
        # Ensure summary is 1 sentence (ends with 。)
        sentences = re.findall(r'[^。]+。', v)
        if len(sentences) != 1:
            raise ValueError(f"Summary must be 1 sentence, got {len(sentences)}")
        return v
    
    rules_content: str = Field(..., min_length=200)
    
    @field_validator('rules_content')
    @classmethod
    def validate_rules_structure(cls, v: str) -> str:
        # Check all 6 sections present
        required_patterns = [
            (r'ゲームの概要', 'Overview section missing'),
            (r'内容物', 'Components section missing'),
            (r'準備', 'Setup section missing'),
            (r'手順', 'Gameplay section missing'),
            (r'終了条件|勝者', 'End-game section missing'),
            (r'戦略|アドバイス', 'Strategy section missing'),
        ]
        for pattern, error_msg in required_patterns:
            if not re.search(pattern, v):
                raise ValueError(error_msg)
        return v
    
    structured_data: StructuredData

class StructuredData(BaseSchema):
    keywords: list[Keyword] = Field(..., min_items=6, max_items=6)
    key_elements: list[KeyElement] = Field(..., min_items=5, max_items=5)
    mechanics: list[str] = Field(..., min_items=3, max_items=6)
    
class Keyword(BaseSchema):
    term: str = Field(..., max_length=20)
    description: str = Field(..., min_length=30, max_length=100)
    
    @field_validator('description')
    @classmethod
    def validate_no_jargon(cls, v: str) -> str:
        # Flag suspicious jargon
        jargon_terms = [
            'メカニクス', 'ワーカープレイスメント', 'ドラフティング',
            'リソースマネジメント', 'トリックテイキング', 'ミープル',
            'エンジンビルディング'
        ]
        if any(term in v for term in jargon_terms):
            raise ValueError(f"Jargon detected in keyword description: {v}")
        return v
```

**Validation benefits**:
- Catches structural violations before database write
- Provides specific error messages to guide correction
- Enables retry with corrected prompt

---

### 3.2 Content Quality Validation (Semantic)

**Technique: Keywords-to-Content Alignment**

```python
def validate_keywords_appear_in_content(rules_content: str, keywords: list[Keyword]) -> tuple[bool, list[str]]:
    """Check that all keywords are referenced in rules_content"""
    missing_keywords = []
    for kw in keywords:
        term = kw.term.replace(' (JA)', '').strip()
        if term not in rules_content:
            missing_keywords.append(term)
    
    if missing_keywords:
        return False, missing_keywords
    return True, []

# Usage in game_service.py
result = await _gemini.generate_structured_json(prompt)
validated_data = GeneratedGameMetadata.model_validate(result)

# Post-validation
is_aligned, missing = validate_keywords_appear_in_content(
    validated_data.rules_content,
    validated_data.structured_data.keywords
)

if not is_aligned:
    logger.warning(f"Keywords not in content: {missing}")
    # Option 1: Reject and re-prompt
    # Option 2: Flag with confidence < 0.7
    validated_data.rules_confidence = 0.5
```

---

### 3.3 Jargon Detection (Regex Patterns)

```python
JARGON_PATTERNS = {
    'katakana_mecha': re.compile(r'ワーカープレイスメント|ドラフティング|エンジン|ミープル|トリック'),
    'abstract_terms': re.compile(r'メカニクスは|ロジックが|システムを|エンジン'),
    'jp_informal': re.compile(r'ですね|ましたね|と思います|かもしれません')
}

def score_jargon(text: str) -> float:
    """Return 0.0 (no jargon) to 1.0 (heavy jargon)"""
    matches = sum(
        len(pattern.findall(text))
        for pattern in JARGON_PATTERNS.values()
    )
    return min(matches / 10, 1.0)  # Normalize to [0, 1]

# Usage
jargon_score = score_jargon(validated_data.summary)
if jargon_score > 0.3:
    logger.warning(f"High jargon content (score={jargon_score}). Requesting regeneration...")
    # Trigger re-generation with stricter anti-jargon prompt
```

---

### 3.4 Completeness Scoring

```python
def score_completeness(data: GeneratedGameMetadata) -> float:
    """Rate 0.0-1.0 how complete the metadata is"""
    scores = []
    
    # Title score (always present if validated)
    scores.append(1.0 if data.title else 0.0)
    
    # Summary score (single sentence)
    summary_sents = len(re.findall(r'[^。]+。', data.summary))
    scores.append(1.0 if summary_sents == 1 else 0.5)
    
    # Rules structure score
    sections = ['ゲームの概要', '内容物', '準備', '手順', '終了条件', '戦略']
    section_count = sum(1 for s in sections if s in data.rules_content)
    scores.append(section_count / len(sections))
    
    # Keyword-to-content alignment
    keywords_in_content = sum(
        1 for kw in data.structured_data.keywords
        if kw.term.replace(' (JA)', '') in data.rules_content
    )
    scores.append(keywords_in_content / len(data.structured_data.keywords))
    
    # Average
    return sum(scores) / len(scores)

# Usage
completeness = score_completeness(validated_data)
if completeness < 0.7:
    logger.warning(f"Low completeness score: {completeness}. Content incomplete.")
    # Flag for human review
```

---

## Part 4: Optimization Examples

### Example 1: Before & After for "Catan"

**BEFORE (Current Approach)**

Input: `generate_metadata("カタン")`

Gemini Output (Inconsistent):
```json
{
  "title": "カタン",
  "summary": "島の開拓と交易のゲーム。リソースマネジメントとネゴシエーション",
  "rules_content": "プレイヤーが島を開拓します...",
  "structured_data": {
    "keywords": [
      { "term": "ワーカープレイスメント", "description": "労働者を配置するゲーム" },
      ...
    ]
  }
}
```

**Problems**:
- Summary: 2 sentences, includes jargon ("リソースマネジメント")
- Keywords: Only 4 items (should be 6)
- Keywords contain jargon without explanation

**AFTER (Optimized Prompt)**

Improved Prompt:
```
Generate metadata for: カタン
SUMMARY RULES: EXACTLY 1 sentence. No jargon. Must answer: "What experience will I have?"
EXAMPLE: 「砂漠の島に入植地を建設して、資源を集めながら友達と競争し、最初に10勝利点を獲得したプレイヤーが勝つゲームです。」

KEYWORDS: EXACTLY 6 terms. NEVER use katakana jargon alone.
EXAMPLE:
{ "term": "入植地", "description": "プレイヤーが砂漠に建設する小さな町。1つの入植地 = 1勝利点。" },
{ "term": "資源カード", "description": "小麦、羊、木などの6種類の資源。これらを集めて町や都市を育てます。" },
...

RULES_CONTENT: 6 sections, Japanese markdown:
1. ゲームの概要と魅力 (2-3 sentences. Explain without jargon.)
2. 内容物 (List what's in the box)
3. 準備 (Step 1, 2, 3... for setup)
4. 手順 (What you do on your turn. 3-5 steps. Explain "交易" as "友達と資源を交換する".)
5. 終了条件 (Game ends when someone reaches 10 points)
6. 戦略アドバイス (3 tips. Focus on fun, not winning.)

Return ONLY valid JSON. No markdown wrapper.
```

Optimized Output:
```json
{
  "title": "カタン",
  "summary": "砂漠の島に入植地を建設して、資源を集めながら友達と競争し、最初に10勝利点を獲得したプレイヤーが勝つゲームです。",
  "rules_content": "【ゲームの概要と魅力】\nカタンは、砂漠の島を一緒に開拓するゲームです。プレイヤーが協力したり競争したりしながら、町や都市を育てていきます。資源を集めて、友達と相談して物を交換しながら、最初に10勝利点を獲得した人が勝ちます。\n\n【内容物】\n- ボード（砂漠の島を表す）\n- 建物コマ（入植地、都市）\n- 資源カード（小麦、羊、木、レンガ、小石）\n- サイコロ2個\n\n【準備手順】\n1. ボードを広げます。\n2. 各プレイヤーが最初の入植地を2つ配置します。\n3. 各入植地の隣の資源カードをもらいます。\n\n【詳細な手順説明】\nあなたのターンに：\n1. サイコロを2個振ります。\n2. 出た数の資源カードをもらいます（例：「5」なら、5の隣にある資源をすべてもらう）。\n3. 友達と資源を交換します（欲しい資源を持っている人に、あなたの資源を渡す）。\n4. 資源を使って建物を建てます（小麦+羊+木+レンガ = 入植地 = 1勝利点）。\n\n【終了条件と勝者】\nサイコロの目が「7」の場合は特別なルール：盗賊という敵キャラが動きます。ゲームは、あなたか友達が10勝利点に最初に達したら終わりです。その人が勝ちです。\n\n【戦略アドバイス】\n1. 友達とたくさん話す。「その資源、交換してもらえない？」と聞くことで、すごく楽しくなります。\n2. 最初の入植地は、異なる資源の隣に置く。そうすれば、色んな資源がもらえます。\n3. 資源がいっぱいになったら、早めに建物に交換する。たくさん持っていると、盗賊に資源を奪われることがあるからです。",
  "structured_data": {
    "keywords": [
      { "term": "入植地", "description": "プレイヤーが砂漠に建設する小さな町。1つ = 1勝利点。" },
      { "term": "資源カード", "description": "小麦、羊、木、レンガ、小石。これらを集めて町を育てます。" },
      { "term": "交易", "description": "友達と資源を交換すること。欲しい資源を手に入れるために相談します。" },
      { "term": "サイコロ", "description": "振って出た数の資源をもらうきっかけになる骨。" },
      { "term": "盗賊", "description": "サイコロで7が出たときに動く敵キャラ。他のプレイヤーの資源を盗むことができます。" },
      { "term": "勝利点", "description": "ゲームで勝つまでのカウント。入植地1個 = 1点。10点に最初に達したら勝ち。" }
    ],
    "key_elements": [
      { "name": "資源の集め方", "type": "mechanic", "reason": "サイコロで毎回違う資源がもらえるので、毎回ドキドキして楽しい。" },
      { "name": "友達との交渉", "type": "mechanic", "reason": "「その資源、交換しない？」と話し合うことで、友達と盛り上がれる。" },
      { "name": "入植地を建てる", "type": "component", "reason": "自分の町を育てるので、ゲームが進むにつれて達成感がある。" },
      { "name": "島のボード", "type": "component", "reason": "いつも違う配置なので、新しいゲームは新しい島で遊ぶ気分になる。" },
      { "name": "盗賊の脅威", "type": "mechanic", "reason": "7が出るとハラハラするので、緊張感が続く。" }
    ],
    "mechanics": ["リソース管理", "交渉", "競争", "運"],
    "best_player_count": "3-4人"
  }
}
```

**Improvements**:
✅ Summary: 1 sentence, no jargon, describes experience
✅ Keywords: Exactly 6, all plain-language, each appears in rules
✅ Rules: 6 clear sections, step-by-step setup, turn flow, end condition
✅ Key elements: 5 items, each explains why it's fun
✅ Passes all Pydantic validators

---

### Example 2: Low-Context Recovery

**Scenario**: User searches for obscure game "ショクセン" (not in database)

**BEFORE**:
```
Gemini: "Error: No context found. Falling back to training data."
Output: Hallucinated data (wrong rules, missing key info)
```

**AFTER (With confidence + fallback)**:

Prompt revision:
```
Query: ショクセン
Context: None (unknown game)

ACTION: If game is unknown:
1. Search for similar games in your knowledge
2. Add confidence scores to indicate uncertainty
3. Mark fields as [AI-INFERRED] if not verified

Example confidence scores:
{
  "title": "ショクセン",
  "title_confidence": 0.9,  // Name from reliable source
  "summary": "...",
  "summary_confidence": 0.4,  // Inferred, not verified
  "rules_content": "...",
  "rules_confidence": 0.2,  // Highly uncertain
  "source_used": "Training data inference"
}

Backend rule: If any confidence < 0.5, flag with ⚠️ for user verification
```

Output:
```json
{
  "title": "ショクセン",
  "title_confidence": 0.9,
  "summary": "[⚠️ AI-generated, may be inaccurate] 食べ物を盗んで逃げるゲーム",
  "summary_confidence": 0.3,
  "rules_confidence": 0.1,
  "note": "Game not found in reliable sources. Content is inferred. Please verify or provide official rules."
}
```

**User sees**: Transparent uncertainty, knows to double-check

---

## Part 5: Implementation Roadmap

### Phase 1: Immediate (1-2 hours)

1. **Update prompts.py with hard constraints**:
   - Add exact counts (6 keywords, 5 elements, etc.)
   - Add exemplar rules with expected format
   - Add inline validation schema description

2. **Enhance Pydantic validators**:
   - Add `@field_validator` for summary sentence count
   - Add rules_content section detection
   - Add keyword count validation (exactly 6)

3. **Add jargon detection**:
   - Implement `score_jargon()` function in game_service.py
   - Flag content with jargon_score > 0.3 for review

### Phase 2: Short-term (2-4 hours)

1. **Implement quality scoring**:
   - `score_completeness()` function
   - `validate_keywords_appear_in_content()` check
   - Store scores in database (add `quality_score` column)

2. **Add confidence signals**:
   - Modify Gemini prompt to include confidence estimates
   - Parse confidence from JSON response
   - Backend filters content by confidence threshold

3. **Create validation dashboard**:
   - Script to audit existing games for jargon/completeness
   - Identify games below quality threshold
   - Bulk re-generation with improved prompt

### Phase 3: Medium-term (4-8 hours)

1. **A/B test prompts**:
   - Create 2-3 prompt variants (current, optimized, ultra-strict)
   - Route 10% of requests to each variant
   - Measure completeness score, jargon score, user feedback

2. **Implement chain-of-thought parsing**:
   - Prompt Gemini to return thinking steps + JSON
   - Parse intermediate validation steps
   - Use for debugging failures

3. **Auto-correction loop**:
   - If quality_score < 0.7, trigger automatic re-generation
   - Use stricter prompt variant
   - Log improvement metrics

---

## Part 6: Validation Checklist for QA

Before deploying improved prompts, validate:

```
[ ] Summary validation:
    [ ] Exactly 1 sentence ending with 。
    [ ] No katakana jargon (run jargon detector)
    [ ] Describes player experience (not mechanics)
    [ ] 50-80 characters

[ ] Rules content:
    [ ] All 6 sections present
    [ ] Step-by-step setup (numbered 1-5)
    [ ] Turn flow is clear
    [ ] End condition stated
    [ ] 3 strategy tips provided
    [ ] No unexplained jargon (auto-flag)

[ ] Keywords:
    [ ] Exactly 6 items
    [ ] Each appears in rules_content
    [ ] Descriptions are plain language
    [ ] Descriptions 30-100 characters

[ ] Key elements:
    [ ] Exactly 5 items
    [ ] Each explains "why is this fun?"
    [ ] Covers mechanics, components, player interaction

[ ] Completeness:
    [ ] Overall score >= 0.8
    [ ] All required fields populated
    [ ] No null values in structured_data

[ ] Testing on 10+ games:
    [ ] Pass rate: >= 90%
    [ ] Jargon score < 0.3: >= 85%
    [ ] User feedback: positive (rough target)
```

---

## Part 7: Monitoring & Iteration

### Key Metrics to Track

1. **Structural Compliance**:
   - % of responses passing Pydantic validation
   - % of responses with all 6 rules sections
   - % with exactly 6 keywords

2. **Content Quality**:
   - Average jargon score (target: < 0.2)
   - Average completeness score (target: > 0.8)
   - % with keyword-to-content alignment

3. **User Experience**:
   - % of regenerations triggered (indicates dissatisfaction)
   - Manual edit frequency per game
   - User feedback sentiment (if available)

### Feedback Loop

```
Generate with improved prompt
    ↓
Score (jargon, completeness, alignment)
    ↓
If score < threshold:
  - Log error patterns
  - Adjust prompt constraint
  - Re-test on next batch
    ↓
Track metrics over time
  - Weekly: % passing validation
  - Monthly: average quality score
  - Quarterly: prompt effectiveness review
```

---

## Summary

**Key Takeaways**:

1. **Hard Constraints Beat Soft Guidance**: Replace "avoid jargon" with regex-backed jargon detection.
2. **Exemplars Over Description**: Show examples of desired output format; LLM mirrors it.
3. **Validation-as-Prompt**: Embed structure rules inside the prompt, not post-processing.
4. **Confidence Transparency**: Let Gemini rate its own certainty; filter unreliable content.
5. **Automated Scoring**: Measure completeness, jargon, alignment continuously.
6. **Iterative Refinement**: Test prompt variants; use metrics to choose winners.

**Expected Outcome**: 85-90% of generated content passes quality validation on first attempt, with dramatic reduction in jargon and structural inconsistency.

