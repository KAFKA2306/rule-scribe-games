import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import ReactMarkdown from 'react-markdown'

export default function GamePage({ slug: propSlug }) {
  const { slug: urlSlug } = useParams()
  const slug = propSlug || urlSlug

  const [game, setGame] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const isStandalone = !propSlug

  useEffect(() => {
    if (!slug) return

    const fetchGame = async () => {
      setLoading(true)
      setError(null)
      try {
        const res = await fetch(`/api/games/${slug}`)
        if (!res.ok) throw new Error('Game not found')

        const data = await res.json()
        const gameData = Array.isArray(data) ? data[0] : (data.game || data)

        if (!gameData) throw new Error('No game data')
        setGame(gameData)
      } catch (e) {
        console.error('Fetch error:', e)
        setError(e.message)
      } finally {
        setLoading(false)
      }
    }

    fetchGame()
  }, [slug])

  if (!slug) return <div className="p-4">Invalid Game URL</div>
  if (loading) return <div className="loading-spinner">読み込み中...</div>
  if (error) return <div className="error-message">{error}</div>
  if (!game) return <div className="not-found">ゲームが見つかりません</div>

  // Safe Data Access
  const title = game.title || game.name || 'Untitled'
  const rules = game.rules_content || game.rules || game.content || ''

  // Determine Rules Type safely
  const isStringRules = typeof rules === 'string'
  const isObjectRules = typeof rules === 'object' && rules !== null

  // Render Content
  const renderRules = () => {
    if (isStringRules) {
      return (
        <div className="markdown-content">
          <ReactMarkdown>{rules}</ReactMarkdown>
        </div>
      )
    }

    if (isObjectRules) {
      return (
        <div className="structured-rules">
          {Object.entries(rules).map(([key, val]) => (
            <div key={key} className="rule-section">
              <h4>{key}</h4>
              <div className="rule-text">
                {typeof val === 'string' ? val : JSON.stringify(val, null, 2)}
              </div>
            </div>
          ))}
        </div>
      )
    }

    return <p className="no-rules">ルール情報がありません</p>
  }

  const content = (
    <div className="game-detail-content">
      <div className="detail-header">
        <h2>{title}</h2>
        {game.source_url && (
          <a href={game.source_url} target="_blank" rel="noreferrer" className="source-badge">
            情報元
          </a>
        )}
      </div>

      {/* Rules */}
      <div className="rules-section">
        <h3>詳しいルール</h3>
        {renderRules()}
      </div>

      {/* Keywords */}
      {game.structured_data?.keywords && (
        <div className="info-section">
          <h3>キーワード</h3>
          <div className="keywords-grid">
            {game.structured_data.keywords.map((kw, i) => (
              <div key={i} className="keyword-item">
                <strong>{kw.term}</strong>
                <span>{kw.description}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Popular Cards */}
      {game.structured_data?.popular_cards && (
        <div className="info-section">
          <h3>人気のカード・要素</h3>
          <div className="cards-grid">
            {game.structured_data.popular_cards.map((card, i) => (
              <div key={i} className="card-item">
                <div className="card-head">
                  <strong>{card.name}</strong>
                  <span className="card-type">{card.type}</span>
                </div>
                <p>{card.reason}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )

  if (isStandalone) {
    return (
      <div className="app-container standalone">
        <header className="main-header">
          <div className="brand">
            <a href="/">♜ ボドゲのミカタ</a>
          </div>
        </header>
        <main className="main-layout single-col">
          <div className="game-detail-pane">
            {content}
          </div>
        </main>
        <footer className="main-footer">
          © {new Date().getFullYear()} ボドゲのミカタ
        </footer>
      </div>
    )
  }

  return content
}
