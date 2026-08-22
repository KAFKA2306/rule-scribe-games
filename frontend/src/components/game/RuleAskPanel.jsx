import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { api } from '../../lib/api'
import { askRule } from '../../lib/ruleAsk.js'

function visibleRuleText(game) {
  return `${game?.rules_content || ''} ${game?.setup_summary || ''} ${game?.gameplay_summary || ''} ${game?.end_game_summary || ''}`.toLowerCase()
}

function hasEditionBoundary(game) {
  const text = visibleRuleText(game)
  return [
    'board game arena',
    'bga',
    'implementation',
    '物理版',
    '別版',
    '版差',
  ].some((marker) => text.includes(marker))
}

function findDisplayedRuleSet(game, rulesets) {
  const text = visibleRuleText(game)
  if (!text) return null

  return rulesets.find((ruleset) => [
    ruleset.edition_label,
    ruleset.platform,
    ruleset.revision_label,
  ].filter(Boolean).some((value) => text.includes(String(value).toLowerCase()))) || null
}

function ruleSetLabel(ruleset) {
  return ruleset.edition_label || ruleset.variant_label || ruleset.platform || ruleset.ruleset_id
}

function ruleSetOptionLabel(ruleset) {
  return [
    ruleSetLabel(ruleset),
    ruleset.platform,
    ruleset.language_code,
    ruleset.revision_label,
  ].filter(Boolean).join(' · ')
}

export function RuleAskPanel() {
  const { slug } = useParams()
  const [question, setQuestion] = useState('')
  const [result, setResult] = useState(null)
  const [ruleSetContext, setRuleSetContext] = useState(null)
  const [selectedRuleSetId, setSelectedRuleSetId] = useState(null)

  useEffect(() => {
    let cancelled = false

    api.get(`/api/games/${slug}`)
      .then(async (gameResponse) => {
        const game = Array.isArray(gameResponse) ? gameResponse[0] : gameResponse?.game || gameResponse
        if (cancelled || !hasEditionBoundary(game)) return

        const rulesetResponse = await api.get(`/api/games/${slug}/rule-sets`)
        if (cancelled || rulesetResponse?.status !== 'available' || !rulesetResponse.rulesets?.length) return

        const displayed = findDisplayedRuleSet(game, rulesetResponse.rulesets)
        setRuleSetContext({ displayed, rulesets: rulesetResponse.rulesets })
        setSelectedRuleSetId(displayed?.ruleset_id || rulesetResponse.rulesets[0].ruleset_id)
      })
      .catch(() => {
        if (!cancelled) {
          setRuleSetContext(null)
          setSelectedRuleSetId(null)
        }
      })

    return () => { cancelled = true }
  }, [slug])

  const selectedRuleSet = ruleSetContext?.rulesets?.find(
    (ruleset) => ruleset.ruleset_id === selectedRuleSetId,
  ) || null
  const selectedUsesDisplayedProjection = Boolean(
    !ruleSetContext?.displayed || selectedRuleSetId === ruleSetContext.displayed.ruleset_id,
  )

  const submit = (event) => {
    event.preventDefault()
    if (!selectedUsesDisplayedProjection) return
    setResult(askRule(slug, question))
  }

  return (
    <section className="pro-card" aria-labelledby="rule-ask-title">
      {ruleSetContext?.rulesets?.length > 1 && (
        <div className="game-empty-note" aria-label="RuleSet context" style={{ marginBottom: '1rem' }}>
          <label htmlFor="rule-set-select"><strong>確認するルール版:</strong></label>{' '}
          <select
            id="rule-set-select"
            value={selectedRuleSetId || ''}
            onChange={(event) => {
              setSelectedRuleSetId(event.target.value)
              setResult(null)
            }}
          >
            {ruleSetContext.rulesets.map((ruleset) => (
              <option key={ruleset.ruleset_id} value={ruleset.ruleset_id}>
                {ruleSetOptionLabel(ruleset)}
              </option>
            ))}
          </select>
          <div style={{ marginTop: '0.5rem' }}>
            表示中の本文: {ruleSetContext.displayed
              ? `${ruleSetOptionLabel(ruleSetContext.displayed)} · ${ruleSetContext.displayed.verification_status}`
              : '既存本文とRuleSetの対応を確認できません'}
          </div>
          {selectedRuleSet && !selectedUsesDisplayedProjection && (
            <div role="status" style={{ marginTop: '0.5rem' }}>
              {ruleSetOptionLabel(selectedRuleSet)} の質問回答用projectionは未整備です。別版の登録済み回答を流用しません。
            </div>
          )}
        </div>
      )}

      <div className="pro-card-title" id="rule-ask-title">ルールを質問</div>
      <p className="summary-text">
        確認済みの登録済みルール根拠だけから回答します。回答は要約で、公式本文そのものではありません。
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
          disabled={!selectedUsesDisplayedProjection}
        />
        <button
          type="submit"
          className="filter-btn"
          disabled={!question.trim() || !selectedUsesDisplayedProjection}
          style={{ marginTop: '0.75rem' }}
        >
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