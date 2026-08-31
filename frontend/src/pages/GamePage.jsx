import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { Helmet } from 'react-helmet-async'
import { api } from '../lib/api'
import { ShareButton, TwitterShareButton } from '../components/game/ShareButtons'
import { TextToSpeech } from '../components/game/TextToSpeech'
import { ExternalLinks } from '../components/game/ExternalLinks'
import { InfographicsGallery } from '../components/game/InfographicsGallery'
import { ConceptGlossary } from '../components/game/ConceptGlossary'
import RuleMarkdown from '../components/game/RuleMarkdown'

const IDENTITY_LABELS = {
  verified: 'IDENTITY VERIFIED',
  needs_review: 'IDENTITY REVIEW REQUIRED',
  unverified: 'IDENTITY UNVERIFIED',
}

const SOURCE_TRUST_LABELS = {
  official_publisher: 'PUBLISHER SOURCE',
  authorized_partner: 'AUTHORIZED PARTNER SOURCE',
  third_party: 'THIRD-PARTY SOURCE',
  unknown: 'SOURCE UNVERIFIED',
}

const REVIEW_LABELS = {
  publisher_reviewed: 'PUBLISHER REVIEWED',
  human_reviewed: 'HUMAN REVIEWED',
  review_required: 'REVIEW REQUIRED',
  ai_draft: 'AI DRAFT',
  unknown: 'REVIEW UNKNOWN',
}

const TAB_HASHES = {
  rules: '#rules',
  coach: '#setup',
  graph: '#connections',
  infographics: '#visual',
}

const HASH_TABS = Object.fromEntries(
  Object.entries(TAB_HASHES).map(([tab, hash]) => [hash, tab]),
)

function formatPlayTime(game) {
  const min = game.play_time_min_minutes
  const max = game.play_time_max_minutes
  if (min != null && max != null) return min === max ? `${min}m` : `${min}-${max}m`
  if (min != null) return `${min}m+`
  if (max != null) return `≤${max}m`
  return game.play_time != null ? `${game.play_time}m` : 'N/A'
}

function isTabAvailable(tab, { hasCoachSummary, hasInfographics }) {
  if (tab === 'coach') return hasCoachSummary
  if (tab === 'infographics') return hasInfographics
  return tab === 'rules' || tab === 'graph'
}

export default function GamePage({ slug: propSlug, initialGame }) {
  const { slug: urlSlug } = useParams()
  const slug = propSlug || urlSlug

  const [game, setGame] = useState(initialGame || null)
  const [loading, setLoading] = useState(!initialGame)
  const [error, setError] = useState(null)
  const [activeTab, setActiveTab] = useState('rules')
  const [connections, setConnections] = useState(null)
  const [connectionsLoading, setConnectionsLoading] = useState(false)
  const [connectionsError, setConnectionsError] = useState(false)

  const BASE_URL = 'https://bodoge-no-mikata.vercel.app'
  const infographicsSourceUrl = game?.infographics_source_url || game?.source_url || null
  const hasInfographics = Boolean(
    game?.infographics &&
    game.infographics_reviewed === true &&
    infographicsSourceUrl,
  )
  const hasCoachSummary = Boolean(
    game?.setup_summary || game?.gameplay_summary || game?.end_game_summary,
  )
  const tabAvailability = { hasCoachSummary, hasInfographics }

  useEffect(() => {
    const fetchData = async () => {
      if (!initialGame) {
        setLoading(true)
        setError(null)
        try {
          const data = await api.get(`/api/games/${slug}`)
          const gameData = Array.isArray(data) ? data[0] : data.game || data
          setGame(gameData)
        } catch (err) {
          console.error(err)
          setError('ゲーム情報の取得に失敗しました')
        } finally {
          setLoading(false)
        }
      }
    }
    fetchData()
  }, [slug, initialGame])

  useEffect(() => {
    if (!game || typeof window === 'undefined') return undefined

    const syncFromLocation = () => {
      const requestedTab = HASH_TABS[window.location.hash]
      if (requestedTab && isTabAvailable(requestedTab, tabAvailability)) {
        setActiveTab(requestedTab)
        return
      }
      setActiveTab('rules')
    }

    syncFromLocation()
    window.addEventListener('popstate', syncFromLocation)
    window.addEventListener('hashchange', syncFromLocation)
    return () => {
      window.removeEventListener('popstate', syncFromLocation)
      window.removeEventListener('hashchange', syncFromLocation)
    }
  }, [game, hasCoachSummary, hasInfographics])

  useEffect(() => {
    if (activeTab !== 'graph') return undefined

    let cancelled = false
    setConnectionsLoading(true)
    setConnectionsError(false)
    setConnections(null)

    api.get(`/api/games/${slug}/connections?limit=8`)
      .then((data) => {
        if (!cancelled) setConnections(data)
      })
      .catch((err) => {
        console.error('Failed to fetch canonical connections:', err)
        if (!cancelled) setConnectionsError(true)
      })
      .finally(() => {
        if (!cancelled) setConnectionsLoading(false)
      })

    return () => { cancelled = true }
  }, [activeTab, slug])

  const navigateToTab = (tab) => {
    if (!isTabAvailable(tab, tabAvailability)) return
    setActiveTab(tab)

    if (typeof window === 'undefined') return
    const hash = TAB_HASHES[tab]
    if (!hash || window.location.hash === hash) return
    window.history.pushState(null, '', `${window.location.pathname}${window.location.search}${hash}`)
  }

  if (loading) {
    return <div className="page-state page-state--loading" role="status">ARCHIVE LOADING...</div>
  }

  if (error || !game) {
    return (
      <div className="page-state page-state--error" role="alert">
        <div>
          <p>{error || 'Game not found'}</p>
          <Link to="/" className="back-link">ディレクトリに戻る</Link>
        </div>
      </div>
    )
  }

  const title = game.title_ja || game.title || 'Untitled'
  const rules = game.rules_content || ''
  const coachSourceUrl = game.source_url || null
  const identityLabel = IDENTITY_LABELS[game.identity_status] || IDENTITY_LABELS.unverified
  const sourceTrustLabel = SOURCE_TRUST_LABELS[game.source_trust] || SOURCE_TRUST_LABELS.unknown
  const reviewLabel = REVIEW_LABELS[game.content_review_status] || REVIEW_LABELS.unknown
  const legacyInfographicsSourceUrl = game.infographics_source_url || coachSourceUrl
  const legacyInfographicsVerified = Boolean(
    game.infographics &&
    game.infographics_reviewed === true &&
    legacyInfographicsSourceUrl,
  )

  const pageTitle = `「${title}」のルール・インスト要約 | ボドゲのミカタ`
  const description = game.summary || `「${title}」の登録済みルール要約と出典情報を確認できます。`
  const gameUrl = `${BASE_URL}/games/${slug}`
  const imageUrl = game.image_url || `${BASE_URL}/assets/no-image.webp`

  return (
    <div className="game-detail-content">
      <Helmet>
        <title>{pageTitle}</title>
        <meta name="description" content={description} />
        <link rel="canonical" href={gameUrl} />
        <meta property="og:image" content={imageUrl} />
      </Helmet>

      <div className="game-page-toolbar">
        <Link to="/" className="back-link" style={{ margin: 0 }}>← DIRECTORY</Link>
        <div className="header-actions">
          <TextToSpeech text={`${title}. ${description}`} />
          <TwitterShareButton slug={slug} title={title} />
          <ShareButton slug={slug} />
        </div>
      </div>

      <div className="game-layout">
        <div className="game-main">
          <div className="game-content">
            <h1 className="game-title">{title}</h1>
            {game.strategy_tier && (
              <div className="tier-badge" style={{ position: 'static', fontSize: '1.2rem', padding: '4px 12px' }}>
                TIER {game.strategy_tier}
              </div>
            )}
          </div>

          <div className="pro-stats-grid" aria-label="ゲーム基本情報">
            <div className="pro-stat-card">
              <div className="pro-stat-label">PLAYERS</div>
              <div className="pro-stat-value">
                {game.min_players != null
                  ? `${game.min_players}${game.max_players != null && game.max_players !== game.min_players ? `-${game.max_players}` : ''}`
                  : 'N/A'}
              </div>
            </div>
            <div className="pro-stat-card">
              <div className="pro-stat-label">TIME</div>
              <div className="pro-stat-value">{formatPlayTime(game)}</div>
            </div>
            <div className="pro-stat-card">
              <div className="pro-stat-label">AGE</div>
              <div className="pro-stat-value">{game.min_age != null ? `${game.min_age}+` : 'N/A'}</div>
            </div>
            <div className="pro-stat-card">
              <div className="pro-stat-label">YEAR</div>
              <div className="pro-stat-value">{game.published_year || 'N/A'}</div>
            </div>
          </div>

          <div className="pro-card pro-card--synopsis">
            <div className="pro-card-title">「{title}」のゲーム概要</div>
            <div className="summary-text">{game.summary || game.description}</div>
          </div>

          <div className="rules-tabs" role="group" aria-label="ゲーム詳細表示">
            <button type="button" aria-pressed={activeTab === 'rules'} className={activeTab === 'rules' ? 'active' : ''} onClick={() => navigateToTab('rules')}>
              詳しいルール
            </button>
            {hasCoachSummary && (
              <button type="button" aria-pressed={activeTab === 'coach'} className={activeTab === 'coach' ? 'active' : ''} onClick={() => navigateToTab('coach')}>
                準備・流れ・終了
              </button>
            )}
            <button type="button" aria-pressed={activeTab === 'graph'} className={activeTab === 'graph' ? 'active' : ''} onClick={() => navigateToTab('graph')}>
              関連ゲーム
            </button>
            {hasInfographics && (
              <button type="button" aria-pressed={activeTab === 'infographics'} className={activeTab === 'infographics' ? 'active' : ''} onClick={() => navigateToTab('infographics')}>
                図で見る
              </button>
            )}
          </div>

          <div className="pro-main-col">
            {activeTab === 'rules' && <RuleMarkdown markdown={rules} />}

            {activeTab === 'coach' && (
              <div className="coach-mode">
                <div className="coach-step active">
                  <span className="coach-step-num">STEP 1</span>
                  <div className="coach-step-title">セットアップ</div>
                  <div style={{ fontSize: '0.95rem', lineHeight: 1.6 }}>
                    {game.setup_summary || 'このゲーム固有のセットアップ要約は未確認です。'}
                  </div>
                </div>

                <div className="coach-step">
                  <span className="coach-step-num">STEP 2</span>
                  <div className="coach-step-title">ゲームの流れ</div>
                  <div style={{ fontSize: '0.95rem', lineHeight: 1.6 }}>
                    {game.gameplay_summary || 'このゲーム固有のゲーム進行要約は未確認です。'}
                  </div>
                </div>

                <div className="coach-step">
                  <span className="coach-step-num">STEP 3</span>
                  <div className="coach-step-title">ゲーム終了</div>
                  <div style={{ fontSize: '0.95rem', lineHeight: 1.6 }}>
                    {game.end_game_summary || 'このゲーム固有の終了条件要約は未確認です。'}
                  </div>
                </div>

                <div style={{ textAlign: 'center', padding: '1rem', color: 'var(--text-muted)', fontSize: '0.8rem' }}>
                  登録済みのゲーム固有要約を表示しています。AI生成・要約を含む場合があり、公式裁定ではありません。
                  {coachSourceUrl && (
                    <>
                      {' '}
                      <a href={coachSourceUrl} target="_blank" rel="noreferrer">出典を確認</a>
                    </>
                  )}
                </div>
              </div>
            )}

            {activeTab === 'graph' && (
              <div className="graph-perspective">
                <div className="pro-card-title">CONNECTIONS (MECHANICAL DNA v2)</div>
                <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '1.5rem' }}>
                  正準Concept IDの共有関係から、説明可能な関連ゲームを算出します。
                </p>

                {connectionsLoading && (
                  <div className="game-empty-state" role="status">関連ゲームを照合しています...</div>
                )}

                {!connectionsLoading && connectionsError && (
                  <div className="game-empty-state" role="status">
                    関連ゲームの正準データを取得できませんでした。
                  </div>
                )}

                {!connectionsLoading && !connectionsError && connections?.status === 'not_available' && (
                  <div className="game-empty-state" role="status">
                    関連ゲームの正準データは未整備です。
                  </div>
                )}

                {!connectionsLoading && !connectionsError && connections?.status === 'available' && connections.connections?.length === 0 && (
                  <div className="game-empty-state" role="status">
                    正準Concept上の関連ゲームはまだ登録されていません。
                  </div>
                )}

                {!connectionsLoading && connections?.status === 'available' && connections.connections?.map((connection) => (
                  <Link to={`/games/${connection.slug}`} key={connection.game_id} className="relation-node" style={{ alignItems: 'flex-start' }}>
                    <img
                      src={connection.image_url || '/assets/no-image.webp'}
                      style={{ width: '48px', height: '48px', objectFit: 'cover', borderRadius: '4px' }}
                      alt={connection.title || ''}
                    />
                    <div style={{ minWidth: 0, flex: 1 }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', gap: '0.75rem', alignItems: 'baseline' }}>
                        <div style={{ fontSize: '0.9rem', fontWeight: 700 }}>{connection.title || connection.slug}</div>
                        <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', whiteSpace: 'nowrap' }}>
                          {Math.round(connection.similarity_score * 100)}% · #{connection.rank}
                        </div>
                      </div>
                      {connection.shared_concepts?.length > 0 && (
                        <div className="game-empty-note" style={{ marginTop: '5px' }}>
                          共有DNA: {connection.shared_concepts.map((concept) => concept.label || concept.concept_id).join(' · ')}
                        </div>
                      )}
                      {connection.hierarchy_matches?.length > 0 && (
                        <div className="game-empty-note" style={{ marginTop: '3px' }}>
                          階層DNA: {connection.hierarchy_matches.map((match) => `${match.source_concept_id} ${match.relation_type} ${match.candidate_concept_id}`).join(' · ')}
                        </div>
                      )}
                    </div>
                  </Link>
                ))}

                {connections?.algorithm_version && (
                  <div className="game-empty-note" style={{ marginTop: '1rem' }}>
                    Algorithm: {connections.algorithm_version}
                  </div>
                )}
              </div>
            )}

            {activeTab === 'infographics' && legacyInfographicsVerified && (
              <InfographicsGallery
                infographics={game.infographics}
                verified={legacyInfographicsVerified}
                sourceUrl={legacyInfographicsSourceUrl}
              />
            )}

            {activeTab === 'data' && <pre className="game-data-dump">{JSON.stringify(game, null, 2)}</pre>}
          </div>
        </div>

        <div className="game-sidebar" aria-label="補足情報">
          <div className="pro-card" aria-label="データ信頼状態">
            <div className="pro-card-title">TRUST &amp; PROVENANCE</div>
            <div className="game-empty-note">{identityLabel}</div>
            <div className="game-empty-note">{sourceTrustLabel}</div>
            <div className="game-empty-note">{reviewLabel}</div>
          </div>

          <ConceptGlossary slug={slug} />

          <div className="pro-card">
            <div className="pro-card-title">LINKS</div>
            <ExternalLinks game={game} />
          </div>
        </div>
      </div>
    </div>
  )
}
