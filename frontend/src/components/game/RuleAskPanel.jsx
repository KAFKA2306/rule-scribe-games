import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { askRule } from '../../lib/ruleAsk.js'

export function RuleAskPanel() {
  const { slug } = useParams()
  const [question, setQuestion] = useState('')
  const [result, setResult] = useState(null)

  const submit = (event) => {
    event.preventDefault()
    setResult(askRule(slug, question))
  }

  return (
    <div className="game-detail-content">
      <section className="pro-card" aria-labelledby="rule-ask-title">
        <div className="pro-card-title" id="rule-ask-title">ルールを質問</div>
        <p className="summary-text">
          確認済みの公式ルール根拠だけから回答します。回答は登録済み要約で、公式本文そのものではありません。
        </p>
        <form onSubmit={submit}>
          <label htmlFor="rule-question" className="sr-only">ルールの質問</label>
          <input
            id="rule-question"
            type="search"
            className="search-input"
            value={question}
            maxLength={200}
            placeholder="例: 同点ならどうなる？"
            onChange={(event) => setQuestion(event.target.value)}
          />
          <button type="submit" className="filter-btn" disabled={!question.trim()} style={{ marginTop: '0.75rem' }}>
            根拠付きで確認
          </button>
        </form>

        {result?.status === 'answered' && (
          <div role="status" style={{ marginTop: '1rem' }}>
            <p>{result.answer}</p>
            {result.evidence.map((item) => (
              <p key={`${item.source_url}-${item.locator}`} style={{ fontSize: '0.85rem' }}>
                根拠: {item.locator} · {item.rule_version}{' '}
                <a href={item.source_url} target="_blank" rel="noreferrer">公式ルールを確認</a>
              </p>
            ))}
          </div>
        )}

        {result?.status === 'unresolved' && (
          <div className="game-empty-state" role="status" style={{ marginTop: '1rem' }}>
            この質問に答えられる確認済み根拠がありません。公式ルール本文を確認してください。
          </div>
        )}
      </section>
    </div>
  )
}
