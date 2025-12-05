import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { Helmet } from 'react-helmet-async'
import ReactMarkdown from 'react-markdown'
import EditGameModal from '../components/EditGameModal'

import { ShareButton, TwitterShareButton } from '../components/game/ShareButtons'
import { RefreshButton } from '../components/game/RefreshButton'
import { TextToSpeech } from '../components/game/TextToSpeech'
import { ExternalLinks } from '../components/game/ExternalLinks'

export default function GamePage({ slug: propSlug }) {
  const { slug: urlSlug } = useParams()
  const slug = propSlug || urlSlug

  const [game, setGame] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [isEditOpen, setIsEditOpen] = useState(false)

  const isStandalone = !propSlug

  useEffect(() => {
    if (!slug) return

    const fetchGame = async () => {
      setLoading(true)
      setError(null)
      const res = await fetch(`/api/games/${slug}`)
      if (!res.ok) throw new Error('Game not found')

      const data = await res.json()
      const gameData = Array.isArray(data) ? data[0] : data.game || data

      if (!gameData) throw new Error('No game data')
      setGame(gameData)
      setLoading(false)
    }

    fetchGame()
  }, [slug])

  const handleSave = async (updatedData) => {
    const res = await fetch(`/api/games/${slug}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(updatedData),
    })

    if (!res.ok) throw new Error('Update failed')

    const data = await res.json()
    setGame(data)
  }

  if (!slug) return <div className="p-4">Invalid Game URL</div>
  if (loading) return <div className="loading-spinner">読み込み中...</div>
  if (error) return <div className="error-message">{error}</div>
  if (!game) return <div className="not-found">ゲームが見つかりません</div>

  const title = game.title_ja || game.title || game.name || 'Untitled'
  const rules = game.rules_content || game.rules || game.content || ''

  const isStringRules = typeof rules === 'string'
  const isObjectRules = typeof rules === 'object' && rules !== null

  const pageTitle = `「${title}」のルールをAIで瞬時に要約 | ボドゲのミカタ`
  const description =
    game.summary ||
    game.description ||
    `「${title}」のルールをAIが日本語で瞬時に要約。セットアップから勝利条件まで、インスト時間を短縮しながらサクッと確認できます。`
  const gameUrl = `https://bodoge-no-mikata.vercel.app/games/${slug}`
  const imageUrl = game.image_url || 'https://bodoge-no-mikata.vercel.app/og-image.png'

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
      <Helmet>
        <title>{pageTitle}</title>
        <meta name="description" content={description} />
        <link rel="canonical" href={gameUrl} />

        { }
        <meta property="og:type" content="article" />
        <meta property="og:url" content={gameUrl} />
        <meta property="og:title" content={pageTitle} />
        <meta property="og:description" content={description} />
        <meta property="og:image" content={imageUrl} />
        <meta property="og:site_name" content="ボドゲのミカタ" />

        { }
        <meta name="twitter:card" content="summary_large_image" />
        <meta name="twitter:url" content={gameUrl} />
        <meta name="twitter:title" content={pageTitle} />
        <meta name="twitter:description" content={description} />
        <meta name="twitter:image" content={imageUrl} />
      </Helmet>
      {game.image_url && (
        <div className="game-hero-image">
          <img
            src={game.image_url}
            alt={title}
            onError={(e) => (e.target.style.display = 'none')}
          />
        </div>
      )}

      <div className="detail-header">
        <h2>{title}</h2>
        <div
          className="header-actions"
          style={{ display: 'flex', alignItems: 'center', gap: '12px' }}
        >
          <button
            className="share-btn"
            onClick={() => setIsEditOpen(true)}
            title="編集"
            aria-label="Edit game"
          >
            ✏️
          </button>
          <TextToSpeech text={description} />
          <RefreshButton slug={slug} onRefresh={() => window.location.reload()} />
          <TwitterShareButton slug={slug} title={title} />
          <ShareButton slug={slug} />
        </div>
      </div>

      <EditGameModal
        game={game}
        isOpen={isEditOpen}
        onClose={() => setIsEditOpen(false)}
        onSave={handleSave}
      />

      {game.summary && (
        <div className="info-section">
          <h3>概要</h3>
          <p style={{ lineHeight: '1.7', color: 'var(--text-muted)' }}>{game.summary}</p>
        </div>
      )}

      {game.video_url && (
        <div className="info-section">
          <h3>ルール動画</h3>
          <div className="video-container" style={{ position: 'relative', paddingBottom: '56.25%', height: 0, overflow: 'hidden', borderRadius: '12px', border: '1px solid var(--border)' }}>
            <iframe
              src={`https://www.youtube.com/embed/${(() => {
                const match = game.video_url.match(/(?:youtu\.be\/|youtube\.com\/watch\?v=)([^&]+)/);
                return match ? match[1] : '';
              })()}`}
              style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%' }}
              frameBorder="0"
              allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
              allowFullScreen
              title="Rule Video"
            />
          </div>
        </div>
      )}

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

      {(game.structured_data?.key_elements || game.structured_data?.popular_cards) && (
        <div className="info-section">
          <h3>重要な要素・カード</h3>
          <div className="cards-grid">
            {(game.structured_data.key_elements || game.structured_data.popular_cards).map(
              (item, i) => (
                <div key={i} className="card-item">
                  <div className="card-head">
                    <strong>{item.name}</strong>
                    <span className="card-type">{item.type}</span>
                  </div>
                  <p>{item.reason}</p>
                </div>
              )
            )}
          </div>
        </div>
      )}

      <ExternalLinks game={game} />
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
