import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { Helmet } from 'react-helmet-async'
import ReactMarkdown from 'react-markdown'
import EditGameModal from '../components/EditGameModal'
import { ShareButton, TwitterShareButton } from '../components/game/ShareButtons'
import { RegenerateButton } from '../components/game/RegenerateButton'
import { TextToSpeech } from '../components/game/TextToSpeech'
import { ExternalLinks } from '../components/game/ExternalLinks'
import { ThinkingMeeple } from '../components/ThinkingMeeple'

export default function GamePage({ slug: propSlug, initialGame }) {
  const { slug: urlSlug } = useParams()
  const slug = propSlug || urlSlug

  const [game, setGame] = useState(initialGame || null)
  const [loading, setLoading] = useState(!initialGame)

  const [heroSrc, setHeroSrc] = useState(slug ? `/assets/games/${slug}.webp` : null)
  const [isEditOpen, setIsEditOpen] = useState(false)

  const isStandalone = !propSlug

  useEffect(() => {
    if (initialGame) return
    const fetchGame = async () => {
      setLoading(true)
      const res = await fetch(`/api/games/${slug}`)
      const data = await res.json()
      const gameData = Array.isArray(data) ? data[0] : data.game || data
      setGame(gameData)
      setLoading(false)
    }
    fetchGame()
  }, [slug, initialGame])

  const BASE_URL = 'https://bodoge-no-mikata.vercel.app'

  const handleSave = async (updatedData) => {
    const res = await fetch(`/api/games/${slug}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(updatedData),
    })

    const data = await res.json()
    setGame(data)
  }

  if (loading)
    return (
      <div className="loading-container">
        <ThinkingMeeple
          text="ミープル君がルールブックを読んでいます... 少々お待ちください"
          imageSrc="/assets/thinking-meeple.webp"
        />
      </div>
    )

  const title = game.title_ja || game.title || game.name || 'Untitled'
  const rules = game.rules_content || game.rules || game.content || ''

  const isStringRules = typeof rules === 'string'
  const isObjectRules = typeof rules === 'object' && rules !== null

  const pageTitle = `「${title}」のルール・インストをAI要約 | 遊び方・3行解説`
  const baseDescription = `「${title}」のルールをAIが瞬時に要約。インスト準備や遊び方の確認に。「${title}」のセットアップ、勝利条件、流れを3行で解説。`
  const description =
    (game.summary || game.description)
      ? `${baseDescription} ${game.summary || game.description}`
      : baseDescription
  const gameUrl = `${BASE_URL}/games/${slug}`
  const imageUrl = game.image_url
    ? (game.image_url.startsWith('http') ? game.image_url : `${BASE_URL}${game.image_url}`)
    : `${BASE_URL}/assets/games/${slug}.webp`

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

  const speechText = (() => {
    let text = `${title}。${game.summary || game.description || ''}`
    if (isStringRules) {
      const cleanRules = rules.replace(/[#*`_~[\]()!]/g, '').replace(/\n+/g, ' ')
      text += ` ルール: ${cleanRules}`
    }
    return text
  })()

  const content = (
    <div className="game-detail-content">
      <Helmet>
        <title>{pageTitle}</title>
        <meta name="description" content={description} />
        <link rel="canonical" href={gameUrl} />

        <meta property="og:type" content="article" />
        <meta property="og:url" content={gameUrl} />
        <meta property="og:title" content={pageTitle} />
        <meta property="og:description" content={description} />
        <meta property="og:image" content={imageUrl} />
        <meta property="og:site_name" content="ボドゲのミカタ" />

        <meta name="twitter:image" content={imageUrl} />

        <script type="application/ld+json">
          {JSON.stringify({
            '@context': 'https://schema.org',
            '@type': 'Game',
            name: title,
            description: description,
            image: imageUrl,
            url: gameUrl,
            numberOfPlayers:
              game.min_players || game.max_players
                ? {
                  '@type': 'QuantitativeValue',
                  minValue: game.min_players,
                  maxValue: game.max_players || game.min_players,
                }
                : undefined,
            audience: game.min_age
              ? {
                '@type': 'PeopleAudience',
                suggestedMinAge: game.min_age,
              }
              : undefined,
            timeRequired: game.play_time
              ? {
                '@type': 'Duration',
                value: `PT${game.play_time}M`,
              }
              : undefined,
            datePublished: game.published_year ? `${game.published_year}` : undefined,
          })}
        </script>
      </Helmet>
      {(heroSrc || game.image_url) && (
        <div className="game-hero-image">
          <img
            src={heroSrc || game.image_url}
            alt={title}
            loading="lazy"
            onError={(e) => {
              if (heroSrc && game.image_url && heroSrc !== game.image_url) {
                setHeroSrc(game.image_url)
              } else {
                e.target.style.display = 'none'
                e.target.parentElement.style.display = 'none'
              }
            }}
          />
        </div>
      )}

      <div className="game-content">
        <h1 className="game-title">{title}</h1>
        <div className="header-actions">
          <TextToSpeech text={speechText} />
          <TwitterShareButton slug={slug} title={title} />
          <ShareButton slug={slug} />
          <button className="share-btn" onClick={() => setIsEditOpen(true)} title="編集">
            ✏️ 編集
          </button>
          <RegenerateButton title={title} onRegenerate={setGame} />
        </div>
      </div>

      <EditGameModal
        key={game.slug}
        game={game}
        isOpen={isEditOpen}
        onClose={() => setIsEditOpen(false)}
        onSave={handleSave}
      />

      {game.summary && (
        <div className="info-section">
          <h3>💡 3行でわかる要約</h3>
          <p className="summary-text">{game.summary}</p>
        </div>
      )}

      {game.video_url && (
        <div className="info-section">
          <h3>ルール動画</h3>
          <div
            className="video-container"
            style={{
              position: 'relative',
              paddingBottom: '56.25%',
              height: 0,
              overflow: 'hidden',
              borderRadius: '12px',
              border: '1px solid var(--border)',
            }}
          >
            <iframe
              src={`https://www.youtube.com/embed/${(() => {
                const match = game.video_url.match(/(?:youtu\.be\/|youtube\.com\/watch\?v=)([^&]+)/)
                return match ? match[1] : ''
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
        <h3>📖 インスト用ルール</h3>
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
            <a
              href="/"
              style={{ display: 'flex', alignItems: 'center', gap: '12px', textDecoration: 'none' }}
            >
              <img
                src="/assets/header-icon.webp"
                alt="Meeple"
                loading="lazy"
                style={{ width: '32px', height: 'auto', marginRight: '-4px' }}
              />
              <span className="logo-icon">♜</span>
              <h1>ボドゲのミカタ</h1>
            </a>
          </div>
          <nav style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            <a href="/data" className="nav-link">
              📊 データ
            </a>
          </nav>
        </header>

        <main className="main-layout single-col">
          <div className="game-detail-pane">{content}</div>
        </main>
        <footer
          className="main-footer"
          style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '12px' }}
        >
          <span>© {new Date().getFullYear()} ボドゲのミカタ</span>
          <img
            src="/assets/footer-logo.jpg"
            alt="Bodoge no Mikata Logo"
            style={{ width: '80px', height: 'auto', borderRadius: '8px', opacity: 0.8 }}
          />
        </footer>
      </div>
    )
  }

  return content
}
