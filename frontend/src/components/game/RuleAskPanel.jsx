import { useEffect, useState } from 'react'

const INTENTS = [
  { id: 'setup', terms: ['準備', 'セットアップ', '配る', '最初に'], section: 'setup' },
  { id: 'end', terms: ['終了', '終わる', '終わり', 'ゲームエンド', '勝利条件'], section: 'end_condition' },
  { id: 'score', terms: ['得点', '点数', 'スコア', '何点', '同点', 'タイブレーク'], section: 'scoring' },
  { id: 'action', terms: ['手番', 'ターン', '何ができ', 'アクション', '行動', '流れ'], section: 'game_flow' },
]

function normalize(text) {
  return String(text || '').normalize('NFKC').toLowerCase().replace(/\s+/g, '')
}

function findSection(question) {
  const normalized = normalize(question)
  return INTENTS.find((intent) => intent.terms.some((term) => normalized.includes(normalize(term))))?.section || 'quick_rules'
}

function answerFromProjection(projection, question) {
  const trimmed = String(question || '').trim()
  if (!projection || projection.status !== 'available' || !trimmed) {
    return { status: 'unresolved', answer: null, evidence: [] }
  }

  const sectionName = findSection(trimmed)
  const preferred = projection[sectionName]
  const fallback = projection.quick_rules
  const items = preferred?.status === 'available' ? preferred.items : fallback?.items || []
  if (!items.length) return { status: 'unresolved', answer: null, evidence: [] }

  return {
    status: 'answered',
    answer: items.map((item) => item.text).join(' '),
    evidence: items.map((item) => ({
      rule_id: item.rule_id,
      claim_id: item.evidence.claim_id,
      source_ids: item.evidence.source_ids,
    })),
  }
}

export function RuleAskPanel({ projection, ruleSet }) {
  const [question, setQuestion] = useState('')
  const [result, setResult] = useState(null)
  const available = projection?.status === 'available'

  useEffect(() => {
    setQuestion('')
    setResult(null)
  }, [projection?.rule_set_id])

  const submit = (event) => {
    event.preventDefault()
    setResult(answerFromProjection(projection, question))
  }

  return (
    <section className="pro-card" aria-labelledby="rule-ask-title">
      <div className="pro-card-title" id="rule-ask-title">ルールを質問</div>
      <p className="summary-text">
        選択中のRuleSetで accepted かつ supporting evidence があるRuleNodeだけから回答します。
      </p>
      {ruleSet && (
        <div className="game-empty-note" style={{ marginBottom: '0.75rem' }}>
          RuleSet: {[ruleSet.edition_label, ruleSet.platform, ruleSet.language_code, ruleSet.revision_label].filter(Boolean).join(' · ')}
        </div>
      )}
      {!available && (
        <div className="game-empty-state" role="status" style={{ marginBottom: '1rem' }}>
          このRuleSetには質問回答へ使える正準projectionがまだありません。
        </div>
      )}
      <form onSubmit={submit}>
        <label htmlFor="rule-question" className="sr-only">ルールの質問</label>
        <input
          id="rule-question"
          type="search"
          className="search-input"
          value={question}
          maxLength={200}
          placeholder="例: いつゲームが終わる？"
          onChange={(event) => setQuestion(event.target.value)}
          disabled={!available}
        />
        <button
          type="submit"
          className="filter-btn"
          disabled={!question.trim() || !available}
          style={{ marginTop: '0.75rem' }}
        >
          根拠付きで確認
        </button>
      </form>

      {result?.status === 'answered' && (
        <div role="status" style={{ marginTop: '1rem' }}>
          <p>{result.answer}</p>
          {result.evidence.map((item) => (
            <div key={`${item.rule_id}-${item.claim_id}`} className="game-empty-note" style={{ marginTop: '6px' }}>
              Rule {item.rule_id} · Claim {item.claim_id} · Sources {item.source_ids.join(', ')}
            </div>
          ))}
        </div>
      )}

      {result?.status === 'unresolved' && (
        <div className="game-empty-state" role="status" style={{ marginTop: '1rem' }}>
          この質問に答えられるaccepted evidence-backed ruleがありません。
        </div>
      )}
    </section>
  )
}
