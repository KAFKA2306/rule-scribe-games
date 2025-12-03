import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import ReactMarkdown from 'react-markdown'

const ShareButton = ({ slug }) => {
  const [copied, setCopied] = useState(false)

  const handleShare = async () => {
    const url = `https://bodoge-no-mikata.vercel.app/games/${slug}`
    try {
      if (navigator.clipboard && navigator.clipboard.writeText) {
        await navigator.clipboard.writeText(url)
      } else {
        const textArea = document.createElement('textarea')
        textArea.value = url
        textArea.style.position = 'fixed'
        document.body.appendChild(textArea)
        textArea.focus()
        textArea.select()
        try {
          document.execCommand('copy')
        } catch (err) {
          console.error('Fallback copy failed', err)
          document.body.removeChild(textArea)
          throw err
        }
        document.body.removeChild(textArea)
      }
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch (err) {
      console.error('Failed to copy:', err)
    }
  }

  return (
    <button
      onClick={handleShare}
      className={`share-btn ${copied ? 'copied' : ''}`}
      title={copied ? 'コピーしました' : 'リンクをコピー'}
      aria-label="Share this game"
    >
      {copied ? '✓' : '🔗'}
    </button>
  )
}

function AffiliateBox({ affiliateUrls, gameTitle }) {
  if (!affiliateUrls) return null
  const { amazon, rakuten, yahoo } = affiliateUrls
  const hasAny = amazon || rakuten || yahoo
  if (!hasAny) return null

  return (
    <div className="affiliate-box">
      {amazon && (
        <a
          href={amazon}
          target="_blank"
          rel="noopener noreferrer sponsored"
          className="affiliate-link amazon"
        >
          Amazonで{gameTitle}を見る
        </a>
      )}
      {rakuten && (
        <a
          href={rakuten}
          target="_blank"
          rel="noopener noreferrer sponsored"
          className="affiliate-link rakuten"
        >
          楽天で{gameTitle}を見る
        </a>
      )}
      {yahoo && (
        <a
          href={yahoo}
          target="_blank"
          rel="noopener noreferrer sponsored"
          className="affiliate-link yahoo"
        >
          Yahoo!で{gameTitle}を見る
        </a>
      )}
    </div>
  )
}

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
        const gameData = Array.isArray(data) ? data[0] : data.game || data

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

  const title = game.title || game.name || 'Untitled'
  const rules = game.rules_content || game.rules || game.content || ''

  const isStringRules = typeof rules === 'string'
  const isObjectRules = typeof rules === 'object' && rules !== null

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
        <div
          className="header-actions"
          style={{ display: 'flex', alignItems: 'center', gap: '12px' }}
        >
          <ShareButton slug={slug} />
        </div>
      </div>

      <div className="rules-section">
        <h3>詳しいルール</h3>
        {renderRules()}
      </div>

      {(game.min_players || game.play_time || game.min_age || game.published_year) && (
        <div className="info-section">
          <h3>基本情報</h3>
          <div className="basic-info-grid">
            {game.min_players && (
              <div className="info-item">
                <strong>プレイ人数</strong>
                <span>
                  {game.min_players}
                  {game.max_players ? ` - ${game.max_players}` : ''}人
                </span>
              </div>
            )}
            {game.play_time && (
              <div className="info-item">
                <strong>プレイ時間</strong>
                <span>{game.play_time}分</span>
              </div>
            )}
            {game.min_age && (
              <div className="info-item">
                <strong>対象年齢</strong>
                <span>{game.min_age}歳〜</span>
              </div>
            )}
            {game.published_year && (
              <div className="info-item">
                <strong>発行年</strong>
                <span>{game.published_year}年</span>
              </div>
            )}
          </div>
        </div>
      )}

      {(game.official_url || game.bgg_url) && (
        <div className="info-section">
          <h3>リンク</h3>
          <div className="links-list">
            {game.official_url && (
              <a href={game.official_url} target="_blank" rel="noreferrer" className="link-item">
                公式サイト
              </a>
            )}
            {game.bgg_url && (
              <a href={game.bgg_url} target="_blank" rel="noreferrer" className="link-item">
                BoardGameGeek
              </a>
            )}
          </div>
        </div>
      )}

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

      {game.affiliate_urls && (
        <AffiliateBox affiliateUrls={game.affiliate_urls} gameTitle={title} />
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
          <div className="game-detail-pane">{content}</div>
        </main>
        <footer className="main-footer">© {new Date().getFullYear()} ボドゲのミカタ</footer>
      </div>
    )
  }

  return content
}
