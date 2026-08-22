import { useMemo } from 'react'

const LABELS = {
  flow: 'ゲームの流れ',
  setup: 'セットアップ',
  scoring: '得点',
}

export function InfographicsGallery({ infographics, verified = false, sourceUrl = null }) {
  const items = useMemo(() => Object.entries(infographics || {}).filter(([, url]) => Boolean(url)), [infographics])

  if (!verified || !sourceUrl || items.length === 0) return null

  return (
    <section className="pro-card" aria-label="ルール図解">
      <div className="pro-card-title">RULE INFOGRAPHICS</div>
      <div className="infographics-grid">
        {items.map(([key, url]) => (
          <figure key={key} className="infographic-item">
            <img src={url} alt={`${LABELS[key] || key}の図解`} loading="lazy" />
            <figcaption>{LABELS[key] || key}</figcaption>
          </figure>
        ))}
      </div>
      <div className="game-empty-note" style={{ marginTop: '0.75rem' }}>
        検証済みソースに紐づく図解のみ表示しています。{' '}
        <a href={sourceUrl} target="_blank" rel="noreferrer">出典を確認</a>
      </div>
    </section>
  )
}
