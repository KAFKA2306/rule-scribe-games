import { useState } from 'react'

export function InfographicsGallery({ infographics, verified = false, sourceUrl = null }) {
  const [currentIndex, setCurrentIndex] = useState(0)

  if (!verified || !sourceUrl) {
    return <p className="no-infographics">図解は検証待ちのため表示していません</p>
  }

  const infographicTypes = [
    { key: 'eyecatch', title: 'このゲームをひと目で', icon: '🃏' },
    { key: 'summary_sheet', title: 'サマリーシート', icon: '📋' },
    { key: 'turn_flow', title: '手番の流れ', icon: '🔄' },
    { key: 'setup', title: 'セットアップ', icon: '⚙️' },
    { key: 'actions', title: 'アクション一覧', icon: '🎲' },
    { key: 'winning', title: '勝利条件', icon: '🏆' },
    { key: 'components', title: 'コンポーネント', icon: '🧩' },
  ]

  const slideKeys = Object.keys(infographics || {})
    .filter((key) => key.startsWith('slide_'))
    .sort((a, b) => {
      const numA = parseInt(a.split('_')[1], 10)
      const numB = parseInt(b.split('_')[1], 10)
      return numA - numB
    })
    .map((key) => ({
      key,
      title: `スライド ${key.split('_')[1]}`,
      icon: '📊',
    }))

  const allTypes = [...infographicTypes, ...slideKeys]
  const available = allTypes.filter((inf) => infographics?.[inf.key])

  if (!available.length) {
    return <p className="no-infographics">図解はまだ利用できません</p>
  }

  const current = available[currentIndex]
  const imageUrl = infographics[current.key]

  return (
    <div className="infographics-gallery">
      <h3>
        {current.icon} {current.title}
      </h3>

      <div className="gallery-image">
        <img
          src={imageUrl}
          alt={current.title}
          loading="lazy"
          onError={(e) => {
            e.target.style.display = 'none'
            e.target.parentElement.innerHTML =
              '<p class="loading-error">画像を読み込めませんでした</p>'
          }}
        />
      </div>

      <div className="gallery-nav">
        <button
          className="gallery-btn"
          onClick={() => setCurrentIndex(Math.max(0, currentIndex - 1))}
          disabled={currentIndex === 0}
          aria-label="前の図解へ"
        >
          ← 前へ
        </button>

        <div className="gallery-dots">
          {available.map((inf, i) => (
            <button
              key={inf.key}
              className={`gallery-dot ${i === currentIndex ? 'active' : ''}`}
              onClick={() => setCurrentIndex(i)}
              aria-label={`${inf.title}へ移動`}
              title={inf.title}
            />
          ))}
        </div>

        <button
          className="gallery-btn"
          onClick={() => setCurrentIndex(Math.min(available.length - 1, currentIndex + 1))}
          disabled={currentIndex === available.length - 1}
          aria-label="次の図解へ"
        >
          次へ →
        </button>
      </div>

      <div className="gallery-counter">
        {currentIndex + 1} / {available.length}
      </div>

      <div className="rule-flow-source">
        出典: <a href={sourceUrl} target="_blank" rel="noreferrer">検証済みルール資料</a>
      </div>
    </div>
  )
}