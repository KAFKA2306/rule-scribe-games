"""
Validation & Scoring Implementation for Gemini Game Metadata

This module provides:
1. Enhanced Pydantic validators for strict structure
2. Content quality scoring (jargon, completeness, alignment)
3. Confidence scoring from LLM responses
4. Diagnostic hooks for debugging failures
"""

import re
from enum import Enum
from pydantic import BaseModel, field_validator, Field


# ============================================================================
# VALIDATORS: Pydantic Field Validation
# ============================================================================

class GameSummary(BaseModel):
    """Validated summary: 1 sentence, no jargon, 50-150 characters."""
    text: str = Field(..., min_length=30, max_length=150)
    
    @field_validator('text')
    @classmethod
    def is_single_sentence(cls, v: str) -> str:
        """Ensure exactly 1 sentence ending with 。"""
        # Count sentences (segments ending with 。)
        sentences = re.findall(r'[^。]+。', v)
        if len(sentences) != 1:
            raise ValueError(
                f"Summary must be exactly 1 sentence ending with 。. "
                f"Found {len(sentences)} sentences."
            )
        return v
    
    @field_validator('text')
    @classmethod
    def no_jargon_keywords(cls, v: str) -> str:
        """Flag high-risk jargon terms in summary."""
        jargon_terms = [
            'メカニクス', 'ワーカープレイスメント', 'ドラフティング',
            'リソースマネジメント', 'エンジン', 'ミープル', 'トリックテイキング',
            'ハンドマネジメント', 'アクションセレクション'
        ]
        found = [term for term in jargon_terms if term in v]
        if found:
            raise ValueError(
                f"Jargon detected in summary (should use plain language): {', '.join(found)}"
            )
        return v


class RulesContent(BaseModel):
    """Validated rules: must contain all 6 sections."""
    text: str = Field(..., min_length=200)
    
    @field_validator('text')
    @classmethod
    def has_all_sections(cls, v: str) -> str:
        """Verify all 6 required sections are present."""
        required_sections = [
            ('ゲームの概要', 'Game Overview'),
            ('内容物', 'Components'),
            ('準備', 'Setup'),
            ('手順', 'Gameplay'),
            ('終了条件', 'End Condition'),
            ('戦略|アドバイス', 'Strategy Tips'),
        ]
        
        missing = []
        for ja_pattern, en_name in required_sections:
            if not re.search(ja_pattern, v):
                missing.append(en_name)
        
        if missing:
            raise ValueError(
                f"Missing required sections: {', '.join(missing)}"
            )
        return v


class Keyword(BaseModel):
    """Validated keyword: term + plain-language description."""
    term: str = Field(..., max_length=20)
    description: str = Field(..., min_length=30, max_length=100)
    
    @field_validator('description')
    @classmethod
    def no_jargon_in_description(cls, v: str) -> str:
        """Description must explain without technical jargon."""
        jargon_terms = [
            'メカニクス', 'ワーカープレイスメント', 'ドラフティング',
            'リソースマネジメント', 'トリックテイキング', 'ミープル',
            'エンジンビルディング', 'ハンドマネジメント'
        ]
        found = [t for t in jargon_terms if t in v]
        if found:
            raise ValueError(
                f"Jargon in keyword description: {', '.join(found)}. "
                f"Use plain language instead."
            )
        return v
    
    @field_validator('term')
    @classmethod
    def max_20_chars(cls, v: str) -> str:
        """Term must be concise (<=20 chars)."""
        if len(v.encode('utf-8')) > 60:  # ~20 chars in UTF-8
            raise ValueError(f"Term too long: {v} ({len(v)} chars)")
        return v


# ============================================================================
# SCORING FUNCTIONS: Content Quality Assessment
# ============================================================================

class JargonLevel(str, Enum):
    """Jargon severity classification."""
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


JARGON_PATTERNS = {
    'katakana_mechanics': {
        'pattern': re.compile(r'ワーカープレイスメント|ドラフティング|エンジン|ミープル|トリックテイキング'),
        'level': 'high',
        'examples': ['ワーカープレイスメント', 'ドラフティング']
    },
    'abstract_mechanics': {
        'pattern': re.compile(r'メカニクスは|ロジックが|システムを|エンジン'),
        'level': 'medium',
        'examples': ['メカニクスは', 'システムを']
    },
    'risky_conjugations': {
        'pattern': re.compile(r'ですね|ましたね|と思います|かもしれません'),
        'level': 'low',
        'examples': ['ですね', 'と思います']
    }
}


def score_jargon(text: str) -> float:
    """
    Analyze jargon density in text.
    
    Returns:
        float: 0.0 (no jargon) to 1.0 (heavy jargon)
    
    Formula:
        - Count matches across all patterns
        - Weight by severity (high=2, medium=1, low=0.5)
        - Normalize to [0, 1]
    """
    weighted_matches = 0
    weights = {'high': 2, 'medium': 1, 'low': 0.5}
    
    for pattern_key, pattern_info in JARGON_PATTERNS.items():
        matches = pattern_info['pattern'].findall(text)
        weight = weights[pattern_info['level']]
        weighted_matches += len(matches) * weight
    
    # Normalize: 20 total weighted matches = score of 1.0
    return min(weighted_matches / 20, 1.0)


def score_rules_completeness(rules_content: str, keywords: list[Keyword]) -> dict[str, float]:
    """
    Measure how complete and well-structured rules content is.
    
    Returns:
        dict with scores:
        - section_coverage: [0, 1] (how many of 6 sections present)
        - keyword_alignment: [0, 1] (% of keywords referenced in rules)
        - length_appropriateness: [0, 1] (is length reasonable for game type)
        - overall: [0, 1] (weighted average)
    """
    scores = {}
    
    # 1. Section coverage
    sections = ['ゲームの概要', '内容物', '準備', '手順', '終了条件', '戦略']
    section_count = sum(1 for s in sections if s in rules_content)
    scores['section_coverage'] = section_count / len(sections)
    
    # 2. Keyword alignment (each keyword should appear in rules)
    keywords_found = 0
    for kw in keywords:
        term = kw.term.replace(' (JA)', '').strip()
        if term in rules_content:
            keywords_found += 1
    scores['keyword_alignment'] = keywords_found / max(len(keywords), 1)
    
    # 3. Length appropriateness
    # Typical rules should be 500-2000 chars
    content_length = len(rules_content)
    if 500 <= content_length <= 2000:
        scores['length_appropriateness'] = 1.0
    elif 200 <= content_length < 500:
        scores['length_appropriateness'] = 0.5  # Too short
    elif content_length > 3000:
        scores['length_appropriateness'] = 0.7  # Too long but acceptable
    else:
        scores['length_appropriateness'] = 0.0
    
    # 4. Overall weighted score
    weights = {
        'section_coverage': 0.4,
        'keyword_alignment': 0.35,
        'length_appropriateness': 0.25
    }
    scores['overall'] = sum(scores[k] * weights[k] for k in weights)
    
    return scores


def score_metadata_coherence(
    title: str, 
    summary: str, 
    rules_content: str,
    keywords: list[Keyword]
) -> dict[str, float]:
    """
    Measure internal consistency of metadata.
    
    Checks:
    - Does summary mention key concepts from keywords?
    - Is title consistent with content?
    - Are key_elements mentioned in rules?
    
    Returns:
        dict with coherence scores
    """
    scores = {}
    
    # 1. Summary-to-keyword coherence
    keyword_terms = [kw.term.replace(' (JA)', '').strip() for kw in keywords]
    mentioned_in_summary = sum(1 for term in keyword_terms if term in summary)
    scores['summary_keyword_mention'] = mentioned_in_summary / max(len(keyword_terms), 1)
    
    # 2. Title-to-rules coherence
    title_words = title.split()
    title_mentions_in_rules = sum(1 for word in title_words if word in rules_content)
    scores['title_rules_mention'] = title_mentions_in_rules / max(len(title_words), 1)
    
    # 3. Overall coherence
    scores['overall'] = (
        scores['summary_keyword_mention'] * 0.6 +
        scores['title_rules_mention'] * 0.4
    )
    
    return scores


def score_confidence(
    jargon_score: float,
    completeness_scores: dict[str, float],
    coherence_scores: dict[str, float]
) -> float:
    """
    Synthesize confidence in the generated metadata.
    
    High confidence (0.8-1.0):
    - Low jargon (< 0.2)
    - High completeness (> 0.8)
    - High coherence (> 0.7)
    
    Low confidence (< 0.5):
    - High jargon (> 0.4)
    - Low completeness (< 0.6)
    - Low coherence (< 0.5)
    
    Returns:
        float: 0.0 (no confidence) to 1.0 (high confidence)
    """
    # Start with completeness as base
    base_confidence = completeness_scores.get('overall', 0.5)
    
    # Penalize high jargon
    jargon_penalty = jargon_score * 0.3
    
    # Boost for coherence
    coherence_boost = coherence_scores.get('overall', 0.5) * 0.2
    
    confidence = base_confidence - jargon_penalty + coherence_boost
    return max(0.0, min(1.0, confidence))


# ============================================================================
# DIAGNOSTIC UTILITIES
# ============================================================================

def diagnose_content(
    title: str,
    summary: str,
    rules_content: str,
    keywords: list[Keyword]
) -> dict:
    """
    Comprehensive diagnostic report on generated metadata.
    
    Returns diagnostic information for debugging quality issues.
    """
    report = {
        'title': title,
        'checks': {}
    }
    
    # 1. Jargon analysis
    jargon_score = score_jargon(summary + " " + rules_content)
    report['checks']['jargon'] = {
        'score': round(jargon_score, 3),
        'level': _jargon_level(jargon_score),
        'status': 'PASS' if jargon_score < 0.3 else 'FAIL'
    }
    
    # 2. Completeness analysis
    completeness = score_rules_completeness(rules_content, keywords)
    report['checks']['completeness'] = {
        'section_coverage': round(completeness['section_coverage'], 2),
        'keyword_alignment': round(completeness['keyword_alignment'], 2),
        'overall_score': round(completeness['overall'], 2),
        'status': 'PASS' if completeness['overall'] >= 0.7 else 'WARN'
    }
    
    # 3. Coherence analysis
    coherence = score_metadata_coherence(title, summary, rules_content, keywords)
    report['checks']['coherence'] = {
        'summary_keyword_mention': round(coherence['summary_keyword_mention'], 2),
        'title_rules_mention': round(coherence['title_rules_mention'], 2),
        'overall_score': round(coherence['overall'], 2),
        'status': 'PASS' if coherence['overall'] >= 0.6 else 'WARN'
    }
    
    # 4. Confidence assessment
    confidence = score_confidence(jargon_score, completeness, coherence)
    report['checks']['confidence'] = {
        'score': round(confidence, 2),
        'recommendation': _confidence_recommendation(confidence)
    }
    
    # 5. Actionable issues
    issues = []
    if jargon_score >= 0.3:
        issues.append("High jargon detected. Regenerate with stricter prompt.")
    if completeness['section_coverage'] < 0.8:
        issues.append("Missing rule sections. Check for gaps in setup/gameplay.")
    if coherence['overall'] < 0.6:
        issues.append("Low coherence. Keywords/title not well-reflected in content.")
    
    report['issues'] = issues
    report['summary'] = _generate_summary(report['checks'])
    
    return report


def _jargon_level(score: float) -> JargonLevel:
    """Convert jargon score to severity level."""
    if score < 0.1:
        return JargonLevel.NONE
    elif score < 0.3:
        return JargonLevel.LOW
    elif score < 0.6:
        return JargonLevel.MEDIUM
    else:
        return JargonLevel.HIGH


def _confidence_recommendation(confidence: float) -> str:
    """Recommendation based on confidence level."""
    if confidence >= 0.85:
        return "SAFE: Display to users"
    elif confidence >= 0.7:
        return "CAUTION: Display with [AI-generated] disclaimer"
    elif confidence >= 0.5:
        return "FLAG: Request human review before display"
    else:
        return "REJECT: Too uncertain. Re-generate with corrected prompt"


def _generate_summary(checks: dict) -> str:
    """Generate human-readable summary of all checks."""
    lines = []
    for check_name, check_data in checks.items():
        if 'status' in check_data:
            status = check_data['status']
            score = check_data.get('score', check_data.get('overall_score'))
            lines.append(f"  {check_name}: {status} (score={score})")
    return "\n".join(lines)


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    # Example: Validate Catan metadata
    
    keywords_example = [
        Keyword(
            term="入植地",
            description="プレイヤーが砂漠に建設する小さな町。1つ = 1勝利点。"
        ),
        Keyword(
            term="資源カード",
            description="小麦、羊、木などの資源。これらを集めて町を育てます。"
        ),
        Keyword(
            term="交易",
            description="友達と資源を交換すること。相談しながら行います。"
        ),
        Keyword(
            term="サイコロ",
            description="振って出た数の資源をもらうきっかけになります。"
        ),
        Keyword(
            term="盗賊",
            description="サイコロで7が出たときに動く敵キャラ。資源を盗みます。"
        ),
        Keyword(
            term="勝利点",
            description="ゲームで勝つまでのカウント。10点に最初に達したら勝ち。"
        ),
    ]
    
    rules_example = """【ゲームの概要と魅力】
カタンは、砂漠の島を一緒に開拓するゲームです。プレイヤーが協力したり競争したりしながら、町や都市を育てていきます。資源を集めて、友達と相談して物を交換しながら、最初に10勝利点を獲得した人が勝ちます。

【内容物】
- ボード（砂漠の島を表す）
- 建物コマ（入植地、都市）
- 資源カード（小麦、羊、木、レンガ、小石）

【準備手順】
1. ボードを広げます。
2. 各プレイヤーが最初の入植地を2つ配置します。

【詳細な手順説明】
あなたのターンに：
1. サイコロを2個振ります。
2. 出た数の資源カードをもらいます。
3. 友達と資源を交換します。
4. 資源を使って建物を建てます。

【終了条件と勝者】
ゲームは、誰かが10勝利点に最初に達したら終わりです。その人が勝ちです。

【戦略アドバイス】
1. 友達とたくさん話す。
2. 最初の入植地は、異なる資源の隣に置く。
3. 資源がいっぱいになったら、早めに建物に交換する。"""
    
    diagnostic = diagnose_content(
        title="カタン",
        summary="砂漠の島に入植地を建設して、資源を集めながら友達と競争し、最初に10勝利点を獲得したプレイヤーが勝つゲームです。",
        rules_content=rules_example,
        keywords=keywords_example
    )
    
    print("=== DIAGNOSTIC REPORT ===")
    print(f"Game: {diagnostic['title']}\n")
    print("Checks:")
    print(diagnostic['summary'])
    print("\nIssues:")
    for issue in diagnostic['issues']:
        print(f"  - {issue}")
    print(f"\nRecommendation: {diagnostic['checks']['confidence']['recommendation']}")
