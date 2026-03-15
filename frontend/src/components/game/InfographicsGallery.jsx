import { useState } from 'react'

export function InfographicsGallery({ infographics }) {
  const [currentIndex, setCurrentIndex] = useState(0)

  const infographicTypes = [
    { key: 'turn_flow', title: '手番の流れ', icon: '🔄' },
    { key: 'setup', title: 'セットアップ', icon: '⚙️' },
    { key: 'actions', title: 'アクション一覧', icon: '🎲' },
    { key: 'winning', title: '勝利条件', icon: '🏆' },
    { key: 'components', title: 'コンポーネント', icon: '🧩' },
  ]

  const available = infographicTypes.filter((inf) => infographics[inf.key])

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
              '<p className="loading-error">画像を読み込めませんでした</p>'
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
    </div>
  )
}
