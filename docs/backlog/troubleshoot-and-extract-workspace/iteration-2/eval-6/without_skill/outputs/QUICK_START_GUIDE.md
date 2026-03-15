# Quick Start: Prompt Optimization & Validation

## TL;DR

**Problem**: Gemini generates valid JSON but inconsistent content (jargon, missing sections, low-quality summaries).

**Solution**: 
1. Replace soft constraints with hard constraints (exact counts, exemplars)
2. Add Pydantic validators to catch structural issues
3. Implement quality scoring (jargon, completeness, coherence)
4. Use confidence signals to flag unreliable content

**Expected Outcome**: 85-90% pass rate on quality validation vs. current 60-70%.

---

## Implementation Steps

### Step 1: Update Prompt (30 minutes)

**File**: `app/prompts/prompts.py`

Replace soft guidance:
```python
# BEFORE (soft)
"keywords: Include 5-8 important game terms"

# AFTER (hard)
"keywords: EXACTLY 6 terms. Format: [{'term': '...', 'description': '...'}, ...]"
```

Add exemplars:
```python
"EXAMPLE summary: 「カタンは、砂漠の島を開拓するゲーム。資源を集めて町を育て、最初に10勝利点を獲得したプレイヤーが勝ちます。」"
```

Add inline validation:
```python
"RULES_CONTENT must have 6 sections: [ゲームの概要], [内容物], [準備], [手順], [終了条件], [戦略]"
```

---

### Step 2: Add Validators (45 minutes)

**File**: `app/models.py`

```python
from pydantic import field_validator, Field

class GeneratedGameMetadata(BaseSchema):
    summary: str = Field(..., min_length=30, max_length=150)
    
    @field_validator('summary')
    @classmethod
    def summary_must_be_single_sentence(cls, v: str) -> str:
        sentences = re.findall(r'[^。]+。', v)
        if len(sentences) != 1:
            raise ValueError(f"Summary must be 1 sentence, got {len(sentences)}")
        return v

class StructuredData(BaseSchema):
    keywords: list[Keyword] = Field(..., min_items=6, max_items=6)
    key_elements: list[KeyElement] = Field(..., min_items=5, max_items=5)
```

Benefit: Validation failures are caught immediately with clear error messages.

---

### Step 3: Add Quality Scoring (1 hour)

**File**: `app/services/game_service.py`

```python
from app.utils.quality_scorer import (
    score_jargon,
    score_rules_completeness,
    score_metadata_coherence,
    score_confidence
)

async def generate_metadata(query: str, context: str | None = None) -> dict[str, object]:
    # ... existing code ...
    result = await _gemini.generate_structured_json(prompt)
    validated_data = GeneratedGameMetadata.model_validate(result)
    
    # NEW: Quality scoring
    jargon_score = score_jargon(validated_data.summary + " " + validated_data.rules_content)
    completeness = score_rules_completeness(validated_data.rules_content, validated_data.structured_data.keywords)
    coherence = score_metadata_coherence(
        validated_data.title,
        validated_data.summary,
        validated_data.rules_content,
        validated_data.structured_data.keywords
    )
    confidence = score_confidence(jargon_score, completeness, coherence)
    
    # Flag low-quality content
    if confidence < 0.7:
        logger.warning(f"Low confidence ({confidence}) for {query}. Flagging for review.")
    
    if jargon_score > 0.3:
        logger.warning(f"High jargon ({jargon_score}) for {query}. Re-prompting...")
        # Option: Retry with stricter anti-jargon prompt
    
    data = validated_data.model_dump()
    data['confidence_score'] = confidence
    data['jargon_score'] = jargon_score
    data['completeness_score'] = completeness['overall']
    
    return data
```

Benefit: You can now filter/flag problematic content automatically.

---

### Step 4: Test on 10 Games (30 minutes)

```bash
# Create test script: test_quality_improvements.py
import asyncio
from app.services.game_service import generate_metadata

test_games = [
    "カタン",
    "スプレンダー",
    "チケット・トゥ・ライド",
    # ... 7 more games
]

for game in test_games:
    result = await generate_metadata(game)
    print(f"{game}:")
    print(f"  Jargon: {result['jargon_score']:.2f}")
    print(f"  Completeness: {result['completeness_score']:.2f}")
    print(f"  Confidence: {result['confidence_score']:.2f}")
```

**Success criteria**:
- 85%+ games pass Pydantic validation
- 80%+ games have jargon_score < 0.3
- 90%+ games have completeness_score >= 0.7

---

## Common Issues & Fixes

### Issue 1: Keywords Not Appearing in Rules

**Diagnosis**: `keyword_alignment` score low (< 0.7)

**Fix**: Update prompt to ensure keywords are mentioned:
```python
"IMPORTANT: Each of your 6 keywords MUST appear at least once in the rules_content. 
Verify before returning JSON."
```

### Issue 2: High Jargon Despite Prompt Saying "Avoid"

**Diagnosis**: `jargon_score` > 0.4

**Fix**: Replace soft guidance with hard examples:
```python
# INSTEAD of "Avoid jargon"
# USE explicit bad/good examples
"❌ DO NOT: ワーカープレイスメントはコアなメカニクスです。
✅ DO: プレイヤーが労働者を配置して資源を集めます。"
```

### Issue 3: Summary Has 2+ Sentences

**Diagnosis**: Pydantic validator rejects: "Summary must be 1 sentence, got 2"

**Fix**: Clarify in prompt:
```python
"Summary: EXACTLY 1 sentence. Format: 「[Core experience]. 」"
```

### Issue 4: Missing Rule Sections

**Diagnosis**: `section_coverage` < 0.8

**Fix**: Require all 6 sections in prompt:
```python
"rules_content MUST include these 6 sections (in any order):
1. ゲームの概要と魅力
2. 内容物
3. 準備手順
4. 詳細な手順説明
5. 終了条件と勝者
6. 戦略アドバイス
Missing any section = FAIL"
```

---

## Metrics Dashboard

Track these weekly:

```
Metric                      Target    How to Measure
─────────────────────────────────────────────────────
Validation Pass Rate        >= 90%    count(confidence_score > 0.7) / total
Jargon Score (avg)          < 0.2     mean(jargon_score) across all games
Completeness Score (avg)    > 0.8     mean(completeness_score) across all games
Keyword Alignment           >= 85%    count(keyword_alignment > 0.85) / total
Summary Quality             >= 90%    count(single_sentence=true) / total

User Metrics (if tracked):
─────────────────────────────────────────────────────
Regeneration Rate           < 10%     count(user_clicked_regenerate) / total_views
Manual Edits Required       < 15%     count(user_edited_content) / total_games
Time-to-Setup (perception)  improved  user feedback / survey
```

---

## Deployment Checklist

Before shipping improved prompts:

- [ ] All 6 prompt improvements implemented in `prompts.py`
- [ ] Pydantic validators added to `app/models.py`
- [ ] Quality scoring integrated into `game_service.py`
- [ ] 10+ games tested; pass rate >= 85%
- [ ] Jargon detector working (false positive check)
- [ ] Confidence scores stored in DB
- [ ] Logging captures failures for analysis
- [ ] Rollback plan in place (can revert to old prompt in 5 min)

---

## A/B Testing (Optional, Phase 2)

Once Phase 1 is stable, test variants:

```python
import random

def choose_prompt_variant(game_slug: str) -> str:
    """Route 10% to experimental, 90% to stable"""
    if random.random() < 0.1:
        return _load_prompt("metadata_generator_v2.strict")
    else:
        return _load_prompt("metadata_generator.generate")
```

Track: Which variant produces higher confidence scores?

---

## Resources

**Implementation Code**: See `validation_implementation.py` in this directory.
- Copy scoring functions into `app/utils/quality_scorer.py`
- Copy validators into `app/models.py`

**Prompt Examples**: See `PROMPT_OPTIMIZATION_GUIDE.md`
- Sections 2.1-2.6: Six engineering techniques with before/after
- Section 4: Real Catan example showing all improvements

**Next Steps**:
1. Week 1: Implement Steps 1-3 above
2. Week 2: Test & monitor metrics
3. Week 3: A/B test prompt variants (optional)
4. Week 4: Analyze results & iterate

---

## Support

If validation fails:
1. Check the specific error message (Pydantic provides clear context)
2. Run diagnostic: `diagnose_content(title, summary, rules_content, keywords)`
3. Adjust prompt constraint that caused failure
4. Re-test on 1-2 games
5. If consistent, re-test on batch of 10

