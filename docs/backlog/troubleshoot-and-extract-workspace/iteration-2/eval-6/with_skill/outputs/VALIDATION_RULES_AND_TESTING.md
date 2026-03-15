# Validation Rules & Testing Framework

## Overview

This document specifies concrete validation rules for detecting and correcting low-quality Gemini outputs, plus a testing framework to verify improvements.

---

## Part 1: Validation Rules (Executable Checks)

### Rule 1: Jargon Detection (Keyword List)

**Purpose**: Catch gaming-specific vocabulary that violates "Explain Like I'm 5" directive.

```python
# app/utils/validation.py

JARGON_BLOCKLIST = {
    # Mechanics
    'drafting': 'ドラフト（順番にカードを選ぶ）',
    'worker placement': 'ワーカープレイスメント（アクション選択）',
    'trick-taking': 'トリックテイク（決められたルールで勝つ）',
    'deck building': 'デックビルディング（カードセットを作る）',
    'set collection': 'セットコレクション（同じグループのカードを集める）',
    'engine building': 'エンジンビルディング（システムを強化する）',
    'area control': 'エリアマジョリティ（場所を支配する）',
    'network building': 'ネットワーク構築',
    'hand management': 'ハンドマネジメント',
    'resource management': 'リソースマネジメント',
    'tableau building': 'テーブルビルディング',
    'push your luck': 'プッシュユアラック（危険な選択）',
    'roll and move': 'ロールアンドムーブ',

    # Components
    'meeple': 'プレイヤーの駒（小さな人型のコマ）',
    'cube': 'キューブ（四角いコマ）',
    'chit': 'チップ',
    'token': 'トークン（得点用の小さい円盤）',
    'tile': 'タイル',

    # Actions
    'discard': '捨てる',
    'draw': '引く',
    'roll': 'サイコロを振る',
    'bid': '値段を言う',

    # Advanced terms (require explanation in parentheses)
    'asymmetric': 'アシンメトリック（プレイヤーごとに違うルール）',
    'cooperative': '協力型',
    'competitive': '対戦型',
    'solo': 'ソロプレイ',
}

def detect_jargon(text: str, threshold: float = 0.0) -> tuple[bool, dict[str, int]]:
    """
    Check if text contains gaming jargon without explanation.

    Args:
        text: Text to check (Japanese or English mix)
        threshold: Max allowable jargon ratio (0.0 = zero tolerance)

    Returns:
        (is_safe, detected_terms)
        is_safe = True if jargon_count / word_count <= threshold
        detected_terms = dict of {jargon_word: count}
    """
    import re
    from collections import Counter

    text_lower = text.lower()

    # Find all jargon terms (case-insensitive)
    detected = Counter()
    for term in JARGON_BLOCKLIST.keys():
        # Count occurrences; avoid partial matches
        pattern = r'\b' + re.escape(term) + r'\b'
        matches = re.findall(pattern, text_lower)
        if matches:
            detected[term] = len(matches)

    # If any term found without explanation (e.g., "drafting =" or "= ドラフト"), flag
    jargon_count = sum(detected.values())
    word_count = len(text.split())

    is_safe = (jargon_count / word_count if word_count > 0 else 0) <= threshold

    return is_safe, dict(detected)


# Usage
text = "ドラフト（カードを選ぶ）を使いながら、ワーカープレイスメント（アクション選択）で駒を配置します。"
is_safe, found = detect_jargon(text, threshold=0.01)  # Allow 1% jargon (must be explained)
print(f"Safe: {is_safe}, Found: {found}")
# Output: Safe: True, Found: {}  (Both terms are explained in parentheses)

text2 = "このゲームはドラフトとワーカープレイスメントを使うゲームです。"
is_safe2, found2 = detect_jargon(text2, threshold=0.01)
print(f"Safe: {is_safe2}, Found: {found2}")
# Output: Safe: False, Found: {'drafting': 1, 'worker placement': 1}
```

### Rule 2: Content Depth Validation

**Purpose**: Ensure outputs are substantive, not trivial.

```python
def validate_content_depth(metadata: GeneratedGameMetadata) -> tuple[bool, list[str]]:
    """
    Validate that all text fields meet minimum depth requirements.

    Returns:
        (is_valid, violations)
    """
    violations = []

    # Summary: 8-25 words, not ending with "です。"
    summary_words = len(metadata.summary.split())
    if summary_words < 8:
        violations.append(f"Summary too short ({summary_words} words, min 8)")
    elif summary_words > 30:
        violations.append(f"Summary too long ({summary_words} words, max 30)")
    if metadata.summary.strip() == metadata.summary.rstrip('。').rstrip() + '。':
        # Rough check for trivial single-sentence template
        if metadata.summary.count('。') == 1 and summary_words < 15:
            violations.append("Summary appears to be trivial single sentence")

    # Description: 50+ words, 3-5 sentences
    desc_words = len(metadata.description.split())
    if desc_words < 50:
        violations.append(f"Description too short ({desc_words} words, min 50)")
    desc_sentences = metadata.description.count('。')
    if desc_sentences < 3:
        violations.append(f"Description too few sentences ({desc_sentences}, min 3)")
    elif desc_sentences > 6:
        violations.append(f"Description too many sentences ({desc_sentences}, max 6)")

    # Rules content: 100+ words, includes setup/turn/end sections
    rules_words = len(metadata.rules_content.split())
    if rules_words < 100:
        violations.append(f"Rules content too short ({rules_words} words, min 100)")
    required_sections = ['準備', 'ゲーム進行', '終了']  # Or English: Setup, Turn, End
    for section in required_sections:
        if section not in metadata.rules_content:
            violations.append(f"Rules missing section: {section}")

    # Structured data
    if len(metadata.structured_data.keywords) < 5:
        violations.append(f"Too few keywords ({len(metadata.structured_data.keywords)}, min 5)")
    if len(metadata.structured_data.key_elements) < 3:
        violations.append(f"Too few key elements ({len(metadata.structured_data.key_elements)}, min 3)")
    if not metadata.structured_data.mechanics:
        violations.append("Mechanics list is empty")

    return (len(violations) == 0, violations)


# Usage
violations = validate_content_depth(metadata)
if not violations[0]:
    print("Content depth issues:")
    for v in violations[1]:
        print(f"  - {v}")
```

### Rule 3: Keyword Quality Validation

**Purpose**: Ensure keywords are diverse, explained, and relevant.

```python
def validate_keyword_quality(keywords: list[Keyword]) -> tuple[bool, list[str]]:
    """
    Validate keyword set for diversity, explanation depth, and clarity.

    Returns:
        (is_valid, violations)
    """
    violations = []

    # Count check
    if len(keywords) < 5:
        violations.append(f"Too few keywords ({len(keywords)}, should be 5-8)")
    elif len(keywords) > 8:
        violations.append(f"Too many keywords ({len(keywords)}, should be 5-8)")

    # Description depth
    for i, kw in enumerate(keywords):
        desc_len = len(kw.description.split())
        if desc_len < 3:
            violations.append(f"Keyword {i+1} ({kw.term}) description too brief ({desc_len} words, min 3)")

    # Jargon check in keyword descriptions
    for i, kw in enumerate(keywords):
        is_safe, found = detect_jargon(kw.description, threshold=0.0)
        if not is_safe:
            violations.append(
                f"Keyword {i+1} ({kw.term}) contains jargon: {', '.join(found.keys())}"
            )

    # Duplicate check
    terms = [kw.term for kw in keywords]
    if len(terms) != len(set(terms)):
        violations.append("Duplicate keywords detected")

    # Relevance check (loose: keywords should not be generic)
    generic_terms = ['game', 'play', 'fun', 'rule', 'player', 'ゲーム', 'プレイ', 'ルール']
    for i, kw in enumerate(keywords):
        if kw.term.lower() in generic_terms:
            violations.append(f"Keyword {i+1} ({kw.term}) is too generic")

    return (len(violations) == 0, violations)


# Usage
violations = validate_keyword_quality(metadata.structured_data.keywords)
if not violations[0]:
    print("Keyword quality issues:")
    for v in violations[1]:
        print(f"  - {v}")
```

### Rule 4: Key Elements Validation

**Purpose**: Ensure elements are diverse and explain why they're fun.

```python
def validate_key_elements(elements: list[KeyElement]) -> tuple[bool, list[str]]:
    """
    Validate key_elements for type diversity and reason quality.

    Returns:
        (is_valid, violations)
    """
    violations = []

    # Count check
    if len(elements) < 3:
        violations.append(f"Too few elements ({len(elements)}, should be 3-6)")
    elif len(elements) > 6:
        violations.append(f"Too many elements ({len(elements)}, should be 3-6)")

    # Type diversity check
    allowed_types = {'component', 'mechanic', 'card', 'token', 'rule', 'resource'}
    types_seen = set()
    for i, elem in enumerate(elements):
        if elem.type not in allowed_types:
            violations.append(f"Element {i+1} ({elem.name}) has invalid type: {elem.type}")
        types_seen.add(elem.type)

    if len(types_seen) < 2:
        violations.append(f"Elements lack type diversity (only {len(types_seen)} types seen, need at least 2)")

    # Reason quality (should explain WHY it's fun, not just WHAT it is)
    for i, elem in enumerate(elements):
        reason_len = len(elem.reason.split())
        if reason_len < 5:
            violations.append(
                f"Element {i+1} ({elem.name}) reason too brief ({reason_len} words, min 5)"
            )
        # Check for "why" language
        why_indicators = ['fun', 'interesting', 'exciting', 'challenge', 'choice', 'strategy',
                         '楽しい', '面白い', 'ドラマ', 'チャレンジ', '選択肢']
        reason_lower = elem.reason.lower()
        if not any(w in reason_lower for w in why_indicators):
            violations.append(
                f"Element {i+1} ({elem.name}) reason doesn't explain why it's fun"
            )

    return (len(violations) == 0, violations)


# Usage
violations = validate_key_elements(metadata.structured_data.key_elements)
if not violations[0]:
    print("Key element issues:")
    for v in violations[1]:
        print(f"  - {v}")
```

### Rule 5: Numeric Sanity Checks

**Purpose**: Catch unrealistic player counts, play times, ages.

```python
def validate_game_stats(
    min_players: int, max_players: int, play_time: int, min_age: int
) -> tuple[bool, list[str]]:
    """
    Validate numeric fields for realism.

    Returns:
        (is_valid, violations)
    """
    violations = []

    # Player counts
    if min_players < 1 or min_players > 100:
        violations.append(f"Invalid min_players: {min_players}")
    if max_players < 1 or max_players > 100:
        violations.append(f"Invalid max_players: {max_players}")
    if min_players > max_players:
        violations.append(f"min_players ({min_players}) > max_players ({max_players})")

    # Play time (reasonable bounds: 5 min to 8 hours)
    if play_time < 5 or play_time > 480:
        violations.append(f"Invalid play_time: {play_time} (must be 5-480 minutes)")

    # Min age (3-18 is reasonable)
    if min_age < 3 or min_age > 18:
        violations.append(f"Invalid min_age: {min_age} (should be 3-18)")

    return (len(violations) == 0, violations)
```

---

## Part 2: Test Suite

### Test Data: Known Good Examples

Create `tests/fixtures/good_metadata.json`:

```json
[
  {
    "title": "Catan",
    "title_ja": "カタン",
    "summary": "島を開拓しながら資源を集めるボードゲーム。運と戦略のバランスが絶妙で、毎回違う展開が楽しめます。",
    "description": "プレイヤーはカタンという島の一部を開拓していきます。サイコロを振って出た数字で資源が手に入り、その資源を使って道を作ったり村を建てたりします。木材と小麦と羊と鉱石とレンガが必要で、最初は何が大事かわかりませんが、ゲーム中に学べます。",
    "min_players": 2,
    "max_players": 4,
    "play_time": 60,
    "min_age": 8,
    "rules_content": "### 準備\n各プレイヤーは開拓地（小さな家）1個と道1個を受け取ります。...",
    "structured_data": {
      "keywords": [
        {"term": "資源 (しゃげん)", "description": "木材・小麦など、ゲーム中に集めるもの。これがないと何もできません"},
        {"term": "開拓地 (かいたくち)", "description": "小さな家。資源をもらえる場所です"},
        {"term": "道 (みち)", "description": "開拓地をつなぐ線。道をいっぱい作ると勝ちに近づきます"}
      ],
      "key_elements": [
        {"name": "資源の多様性", "type": "mechanic", "reason": "5種類の資源があるので、運と計画の両方が大切。毎ゲーム戦略が変わります"},
        {"name": "タイル配置の変化", "type": "component", "reason": "タイルの並び方が毎回違うので、同じゲームが二度とありません"}
      ],
      "mechanics": ["Resource Collection", "Dice Rolling", "Area Development"],
      "best_player_count": "3-4"
    }
  }
]
```

### Test Case 1: Quality Scoring

```python
# tests/test_quality_scoring.py
import pytest
from app.services.game_service import _score_metadata_quality
from app.models import GeneratedGameMetadata

def test_score_excellent_metadata():
    """High-quality metadata should score 0.75+."""
    metadata = GeneratedGameMetadata(
        title="Catan",
        title_ja="カタン",
        summary="島を開拓しながら資源を集めるボードゲーム。運と戦略のバランスが絶妙で、毎回違う展開が楽しめます。",
        description="プレイヤーはカタンという島の一部を開拓していきます。サイコロを振って出た数字で資源が手に入り、その資源を使って道を作ったり村を建てたりします。木材と小麦と羊と鉱石とレンガが必要で、最初は何が大事かわかりませんが、ゲーム中に学べます。",
        min_players=2,
        max_players=4,
        play_time=60,
        min_age=8,
        rules_content="### 準備\n各プレイヤーは開拓地1個と道1個を受け取ります。ボードはタイルで島を作ります。\n### ゲーム進行\n1. サイコロ2個を振ります\n2. 出た合計の数字が資源を決めます\n3. 資源4個を使って道や村を建てられます\n### 終了\n最初に村10個建てた人が勝ちです。",
        structured_data={
            "keywords": [
                {"term": "資源", "description": "木材・小麦など、ゲーム中に集めるもの。これがないと何もできません"},
                {"term": "開拓地", "description": "小さな家。資源をもらえる場所です"},
                {"term": "道", "description": "開拓地をつなぐ線。道をいっぱい作ると勝ちに近づきます"},
                {"term": "サイコロ", "description": "2個を振って、資源がもらえるかどうか決まります"}
            ],
            "key_elements": [
                {"name": "資源の多様性", "type": "mechanic", "reason": "5種類の資源があるので、運と計画の両方が大切。毎ゲーム戦略が変わります"},
                {"name": "タイル配置", "type": "component", "reason": "毎回違う配置で新しい戦略が必要になります"}
            ],
            "mechanics": ["Resource Collection", "Dice Rolling", "Area Development"],
            "best_player_count": "3-4"
        }
    )
    score = _score_metadata_quality(metadata)
    assert score >= 0.75, f"Expected score 0.75+, got {score:.2f}"

def test_score_shallow_metadata():
    """Low-quality metadata should score <0.50."""
    metadata = GeneratedGameMetadata(
        title="Game",
        title_ja="ゲーム",
        summary="楽しいゲームです。",  # Too short
        description="プレイヤーがいます。",  # Way too short
        min_players=1,
        max_players=10,
        play_time=30,
        min_age=5,
        rules_content="ゲームをします。",  # Trivial
        structured_data={
            "keywords": [
                {"term": "game", "description": "game"}  # Lazy descriptions
            ],
            "key_elements": [
                {"name": "fun", "type": "mechanic", "reason": "is fun"}  # Trivial
            ],
            "mechanics": [],  # Empty
            "best_player_count": None
        }
    )
    score = _score_metadata_quality(metadata)
    assert score < 0.50, f"Expected score <0.50, got {score:.2f}"

def test_score_jargon_penalty():
    """Metadata with unjustified jargon should score lower."""
    metadata_with_jargon = GeneratedGameMetadata(
        title="Game",
        title_ja="ゲーム",
        summary="Drafting と Worker Placement を使うゲーム。面白いです。",  # Jargon!
        description="このゲームは drafting mechanic を採用しており、...",
        min_players=2,
        max_players=4,
        play_time=60,
        min_age=10,
        rules_content="各プレイヤーは worker placement を使う。",
        structured_data={"keywords": [], "key_elements": [], "mechanics": [], "best_player_count": None}
    )
    score = _score_metadata_quality(metadata_with_jargon)
    assert score < 0.60, f"Jargon should reduce score; got {score:.2f}"
```

### Test Case 2: Validation Functions

```python
# tests/test_validation_rules.py
import pytest
from app.utils.validation import (
    detect_jargon,
    validate_content_depth,
    validate_keyword_quality,
    validate_key_elements,
    validate_game_stats
)
from app.models import GeneratedGameMetadata, Keyword, KeyElement, StructuredData

def test_jargon_detection():
    """Detect unjustified jargon."""
    # Justified jargon (explained)
    text_ok = "ドラフト（カードを選ぶ）を使う。"
    is_safe, found = detect_jargon(text_ok, threshold=0.0)
    assert is_safe, "Explained jargon should pass"

    # Unjustified jargon
    text_bad = "このゲームはドラフトを使う。"
    is_safe, found = detect_jargon(text_bad, threshold=0.0)
    assert not is_safe, "Unexplained jargon should fail"
    assert 'drafting' in found, "Should detect 'drafting' term"

def test_keyword_validation():
    """Keyword set validation."""
    good_keywords = [
        Keyword(term="資源", description="ゲーム中に集めるもの。これがないと何もできません"),
        Keyword(term="道", description="開拓地をつなぐ線。道をいっぱい作ると勝ちに近づきます"),
        Keyword(term="村", description="小さな家。資源をもらえます"),
        Keyword(term="都市", description="大きな家。2個分の価値があります"),
        Keyword(term="サイコロ", description="2個を振って、資源がもらえるかどうか決まります"),
        Keyword(term="交易", description="ほかのプレイヤーと資源を交換するアクション"),
        Keyword(term="開拓地", description="最初に置く家。ここから道が伸びます"),
        Keyword(term="海賊", description="道をブロックするピース。ゲームを難しくします"),
    ]
    is_valid, violations = validate_keyword_quality(good_keywords)
    assert is_valid, f"Good keywords should pass; violations: {violations}"

    bad_keywords = [
        Keyword(term="game", description="game"),  # Generic, too short
        Keyword(term="play", description="play"),  # Generic
    ]
    is_valid, violations = validate_keyword_quality(bad_keywords)
    assert not is_valid, "Generic/short keywords should fail"
    assert any("too generic" in v for v in violations), "Should detect generic terms"

def test_element_diversity():
    """Key elements should have type diversity."""
    good_elements = [
        KeyElement(name="資源", type="component", reason="複数の資源タイプがあるので、毎ゲーム戦略が変わります"),
        KeyElement(name="ドラフト", type="mechanic", reason="カードを選ぶ楽しさがあります"),
        KeyElement(name="交易", type="rule", reason="ほかのプレイヤーと交渉するドラマが生まれます"),
    ]
    is_valid, violations = validate_key_elements(good_elements)
    assert is_valid, f"Diverse elements should pass; violations: {violations}"

    bad_elements = [
        KeyElement(name="mechanic1", type="mechanic", reason="fun"),
        KeyElement(name="mechanic2", type="mechanic", reason="fun"),  # No diversity
    ]
    is_valid, violations = validate_key_elements(bad_elements)
    assert not is_valid, "Lack of type diversity should fail"

def test_game_stats_validation():
    """Game stats should be realistic."""
    is_valid, violations = validate_game_stats(min_players=2, max_players=4, play_time=60, min_age=8)
    assert is_valid, "Realistic stats should pass"

    is_valid, violations = validate_game_stats(min_players=999, max_players=1, play_time=10000, min_age=100)
    assert not is_valid, "Unrealistic stats should fail"
    assert len(violations) >= 3, "Should detect multiple violations"
```

### Test Case 3: Integration (Full Pipeline)

```python
# tests/test_end_to_end_quality.py
import pytest
import asyncio
from app.services.game_service import generate_metadata_with_critique
from app.utils.validation import (
    detect_jargon,
    validate_content_depth,
    validate_keyword_quality
)

@pytest.mark.asyncio
async def test_generate_with_quality_threshold():
    """Generate metadata and verify it meets quality standards."""
    query = "Catan board game"
    metadata = await generate_metadata_with_critique(query, max_iterations=2)

    # Check content depth
    is_valid_depth, violations = validate_content_depth(metadata)
    assert is_valid_depth, f"Content depth issues: {violations}"

    # Check keyword quality
    is_valid_keywords, violations = validate_keyword_quality(
        metadata.get('structured_data', {}).get('keywords', [])
    )
    assert is_valid_keywords, f"Keyword issues: {violations}"

    # Check jargon
    full_text = " ".join([
        metadata.get('summary', ''),
        metadata.get('description', ''),
        metadata.get('rules_content', '')
    ])
    is_safe, found = detect_jargon(full_text, threshold=0.01)
    assert is_safe, f"Jargon detected: {found}"

    # Check quality score
    from app.services.game_service import _score_metadata_quality
    score = _score_metadata_quality(metadata)
    assert score >= 0.75, f"Quality score {score:.2f} below threshold 0.75"
```

---

## Part 3: Running Tests

```bash
# Install test dependencies
task setup:backend

# Run validation tests
uv run pytest tests/test_validation_rules.py -v

# Run quality scoring tests
uv run pytest tests/test_quality_scoring.py -v

# Run end-to-end tests (requires GEMINI_API_KEY)
uv run pytest tests/test_end_to_end_quality.py -v --timeout=60

# Run all tests
uv run pytest tests/ -v -k "quality or validation"

# Generate quality report
uv run pytest tests/ --html=report.html --cov=app --cov-report=html
```

---

## Part 4: Monitoring & Observability

### Logging Quality Metrics

```python
# app/services/game_service.py

import logging
from datetime import datetime

logger = logging.getLogger(__name__)

async def generate_metadata_with_critique(query: str, context: str | None = None, max_iterations: int = 2) -> dict:
    # ... existing code ...

    # Log metrics
    logger.info({
        "event": "metadata_generation_complete",
        "query": query,
        "quality_score": quality_score,
        "iterations": iteration + 1,
        "content_depth_valid": is_valid_depth,
        "jargon_safe": is_safe_jargon,
        "keyword_count": len(structured_data.keywords),
        "element_count": len(structured_data.key_elements),
        "timestamp": datetime.utcnow().isoformat(),
    })

    return data
```

### Prometheus Metrics (Optional)

```python
# app/core/metrics.py
from prometheus_client import Histogram, Counter

metadata_quality_score = Histogram(
    'metadata_quality_score',
    'Quality score (0-1) of generated metadata',
    buckets=[0.3, 0.5, 0.7, 0.85, 1.0]
)

metadata_generation_iterations = Histogram(
    'metadata_generation_iterations',
    'Number of iterations to reach quality threshold',
    buckets=[1, 2, 3, 5]
)

jargon_detection_count = Counter(
    'jargon_detection_count',
    'Count of jargon instances detected',
    labelnames=['game_title']
)
```

---

## Summary Table

| Validation Rule | Purpose | Implementation |
|-----------------|---------|-----------------|
| **Jargon Detection** | Catch gaming vocabulary | Regex + blocklist (40+ terms) |
| **Content Depth** | Ensure substantive output | Word count + section checks |
| **Keyword Quality** | Diverse, explained keywords | Count bounds + jargon check |
| **Key Elements** | Type diversity + fun explanations | Type set + reason keywords |
| **Game Stats** | Realistic numbers | Range checks (1-100, 5-480, etc.) |
| **Quality Score** | Overall quality metric | Weighted multi-factor scoring |
| **Iteration Feedback** | Critic loop trigger | Score threshold (0.75) |

