export function ScoringBreakdown({ scoring }) {
  if (!scoring) return null

  return (
    <details className="scoring-breakdown" data-testid="scoring-breakdown">
      <summary>得点の数え方</summary>
      <p className="scoring-summary">{scoring.summary}</p>

      {scoring.rules?.length > 0 && (
        <div className="scoring-rule-list">
          {scoring.rules.map((rule) => (
            <details className="scoring-rule" key={rule.label}>
              <summary>{rule.label}</summary>
              <p>{rule.detail}</p>
            </details>
          ))}
        </div>
      )}

      {scoring.example && (
        <div className="scoring-example" aria-label={scoring.example.label}>
          <div className="quick-rules-kicker">{scoring.example.label}</div>
          <div className="scoring-example-total">合計 {scoring.example.total}点</div>
          <ul>
            {scoring.example.items.map((item) => <li key={item}>{item}</li>)}
          </ul>
        </div>
      )}
    </details>
  )
}
