import './rule-guide.css'

export function RuleFlowDiagram({ guide }) {
  if (!guide?.flow?.length) {
    return <p className="no-infographics">検証済みの図解はまだ利用できません</p>
  }

  return (
    <section className="rule-flow" aria-label="ルールフロー" data-testid="rule-flow-diagram">
      <div className="rule-flow-header">
        <div>
          <div className="quick-rules-kicker">RULE FLOW</div>
          <h2 className="rule-flow-title">手番からゲーム終了まで</h2>
        </div>
        <div className="rule-verified-badge">公式ルール確認済み</div>
      </div>

      <ol className="rule-flow-list">
        {guide.flow.map((node, index) => (
          <li className={`rule-flow-node rule-flow-node--${node.kind}`} key={node.id}>
            <span className="rule-flow-step-number" aria-hidden="true">{index + 1}</span>
            <div className="rule-flow-node-label">{node.label}</div>
            {node.note && <div className="rule-flow-node-note">注意: {node.note}</div>}
            {node.branches?.length > 0 && (
              <div className="rule-flow-branches">
                {node.branches.map((branch) => (
                  <div className="rule-flow-branch" key={`${node.id}-${branch.label}`}>
                    <strong>{branch.label}</strong>
                    <span>{branch.detail}</span>
                  </div>
                ))}
              </div>
            )}
          </li>
        ))}
      </ol>

      <div className="rule-flow-source">
        出典: <a href={guide.source.url} target="_blank" rel="noreferrer">{guide.source.label}</a>
      </div>
    </section>
  )
}
