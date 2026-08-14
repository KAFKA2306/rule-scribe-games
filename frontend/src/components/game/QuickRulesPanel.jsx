import { ScoringBreakdown } from './ScoringBreakdown'
import './rule-guide.css'

export function QuickRulesPanel({ guide, onShowFlow, onShowRules }) {
  if (!guide) {
    return (
      <section className="quick-rules-panel quick-rules-unavailable" aria-label="すぐ遊ぶ">
        <div className="quick-rules-kicker">QUICK RULES</div>
        <div className="quick-rules-title">検証済みの要約はまだありません</div>
        <p style={{ marginTop: '0.55rem', lineHeight: 1.6 }}>
          未確認内容は推測表示しません。詳しいルールと出典を確認してください。
        </p>
        {onShowRules && (
          <div className="quick-rules-actions">
            <button type="button" className="quick-rule-action" onClick={onShowRules}>詳しいルールを見る</button>
          </div>
        )}
      </section>
    )
  }

  return (
    <section className="quick-rules-panel" aria-label="すぐ遊ぶ" data-testid="quick-rules-panel">
      <div className="quick-rules-header">
        <div>
          <div className="quick-rules-kicker">QUICK RULES</div>
          <h2 className="quick-rules-title">卓上ですぐ確認</h2>
        </div>
        <div className="rule-verified-badge">公式ルール確認済み</div>
      </div>

      <div className="quick-rules-grid">
        <article className="quick-rule-card">
          <div className="quick-rule-label">勝つには？</div>
          <p>{guide.quick.win}</p>
        </article>

        <article className="quick-rule-card quick-rule-card--primary">
          <div className="quick-rule-label">今の手番ですること</div>
          <ol className="quick-turn-steps">
            {guide.quick.turnSteps.map((step) => <li key={step}>{step}</li>)}
          </ol>
          {guide.quick.actions?.length > 0 && (
            <ul className="quick-check-list" style={{ marginTop: '0.65rem' }}>
              {guide.quick.actions.map((action) => <li key={action}>{action}</li>)}
            </ul>
          )}
        </article>

        <article className="quick-rule-card">
          <div className="quick-rule-label">手番終了時に確認</div>
          <ul className="quick-check-list">
            {guide.quick.turnEndChecks.map((check) => <li key={check}>{check}</li>)}
          </ul>
        </article>

        <article className="quick-rule-card">
          <div className="quick-rule-label">いつ終わる？</div>
          <p>{guide.quick.end}</p>
        </article>
      </div>

      <ScoringBreakdown scoring={guide.scoring} />

      <div className="quick-rules-actions">
        {onShowFlow && <button type="button" className="quick-rule-action" onClick={onShowFlow}>図で見る</button>}
        {onShowRules && <button type="button" className="quick-rule-action" onClick={onShowRules}>詳しいルール</button>}
        <a className="quick-rule-action" href={guide.source.url} target="_blank" rel="noreferrer">公式出典</a>
      </div>

      <div className="quick-rules-source">
        {guide.source.label} / rule version: {guide.ruleVersion}。要約は公式裁定そのものではありません。
      </div>
    </section>
  )
}
