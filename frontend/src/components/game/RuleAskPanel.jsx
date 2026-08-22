import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { api } from '../../lib/api'
import { askRule } from '../../lib/ruleAsk.js'

function findDisplayedRuleSet(game, rulesets) {
  const visibleRuleText = `${game?.rules_content || ''} ${game?.setup_summary || ''} ${game?.gameplay_summary || ''} ${game?.end_game_summary || ''}`.toLowerCase()
  if (!visibleRuleText) return null

  return rulesets.find((ruleset) => [
    ruleset.edition_label,
    ruleset.platform,
    ruleset.revision_label,
  ].filter(Boolean).some((value) => visibleRuleText.includes(String(value).toLowerCase()))) || null
}

function ruleSetLabel(ruleset) {
  return ruleset.edition_label || ruleset.variant_label || ruleset.platform || ruleset.ruleset_id
}

export function RuleAskPanel({ game }) {
  const { slug } = useParams()
  const [question, setQuestion] = useState('')
  const [result, setResult] = useState(null)
  const [ruleSetContext, setRuleSetContext] = useState(null)

  useEffect(() => {
    let cancelled = false

    api.get(`/api/games/${slug}/rule-sets`)
      .then((rulesetResponse) => {
        if (cancelled || rulesetResponse?.status !== 'available' || !rulesetResponse.rulesets?.length) return
        const displayed = findDisplayedRuleSet(game, rulesetResponse.rulesets)
        setRuleSetContext({ displayed, rulesets: rulesetResponse.rulesets })
      })
      .catch(() => {
        if (!cancelled) setRuleSetContext(null)
      })

    return () => { cancelled = true }
  }, [game, slug])

  const submit = (event) => {
    event.preventDefault()
    setResult(askRule(slug, question))
  }

  return (
    <section className="pro-card" aria-labelledby="rule-ask-title">
      {ruleSetContext?.rulesets?.length > 1 && (
        <div className="game-empty-note" aria-label="RuleSet context" style={{ marginBottom: '1rem' }}>
          <strong>表示中のルール版:</strong>{' '}
          {ruleSetContext.displayed ? (
            <>
              {ruleSetLabel(ruleSetContext.displayed)}
              {ruleSetContext.displayed.platform ? ` · ${ruleSetContext.displayed.platform}` : ''}
              {ruleSetContext.displayed.language_code ? ` · ${ruleSetContext.displayed.language_code}` : ''}
              {ruleSetContext.displayed.revision_label ? ` · ${ruleSetContext.displayed.revision_label}` : ''}
              {` · ${ruleSetContext.displayed.verification_status}`}
            </>
          ) : (
            '既存本文とRuleSetの対応を確認できません'
          )}
          <div style={{ marginTop: '0.5rem' }}>
            別版: {ruleSetContext.rulesets
              .filter((ruleset) => ruleset.ruleset_id !== ruleSetContext.displayed?.ruleset_id)
              .map((ruleset) => `${ruleSetLabel(ruleset)}${ruleset.platform ? ` · ${ruleset.platform}` : ''}${ruleset.language_code ? ` · ${ruleset.language_code}` : ''} · ${ruleset.verification_status}`)
              .join(' / ')}
          </div>
          <div style={{ marginTop: '0.5rem' }}>
            版ごとのRuleSetは分離されています。別版の情報を現在表示中の本文へ自動的に混ぜません。
          </div>
        </div>
      )}

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
  )
}
