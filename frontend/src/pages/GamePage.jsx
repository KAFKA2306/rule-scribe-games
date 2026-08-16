import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { Helmet } from 'react-helmet-async'
import ReactMarkdown from 'react-markdown'
import { api } from '../lib/api'
import { getCuratedRuleGuide } from '../lib/curatedRuleGuides'
import { ShareButton, TwitterShareButton } from '../components/game/ShareButtons'
import { TextToSpeech } from '../components/game/TextToSpeech'
import { ExternalLinks } from '../components/game/ExternalLinks'
import { InfographicsGallery } from '../components/game/InfographicsGallery'
import { QuickRulesPanel } from '../components/game/QuickRulesPanel'
import { RuleFlowDiagram } from '../components/game/RuleFlowDiagram'
import { ConceptGlossary } from '../components/game/ConceptGlossary'

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
  const sd = game.structured_data || {}
  const coachSourceUrl = game.source_url || null
  const identityLabel = IDENTITY_LABELS[game.identity_status] || IDENTITY_LABELS.unverified
  const sourceTrustLabel = SOURCE_TRUST_LABELS[game.source_trust] || SOURCE_TRUST_LABELS.unknown
  const reviewLabel = REVIEW_LABELS[game.content_review_status] || REVIEW_LABELS.unknown
  const ruleGuide = getCuratedRuleGuide(slug)
  const legacyInfographicsSourceUrl = game.infographics_source_url || coachSourceUrl
  const legacyInfographicsVerified = Boolean(
    game.infographics &&
    game.infographics_reviewed === true &&
    legacyInfographicsSourceUrl,
  )
  const hasRuleFlow = Boolean(ruleGuide?.flow?.length)
  const hasInfographics = hasRuleFlow || legacyInfographicsVerified

  const pageTitle = `「${title}」のルール・戦略・インスト要約 | ボドゲのミカタ`
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
          <TextToSpeech text={`${title}. ${ruleGuide?.quick?.turnSteps?.join(' ') || description}`} />
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

          <QuickRulesPanel
            guide={ruleGuide}
            onShowFlow={hasInfographics ? () => setActiveTab('infographics') : null}
            onShowRules={() => setActiveTab('rules')}
          />

          <div className="rules-tabs" role="tablist" aria-label="ゲーム詳細表示">
            <button role="tab" aria-selected={activeTab === 'rules'} className={activeTab === 'rules' ? 'active' : ''} onClick={() => setActiveTab('rules')}>
              詳しいルール <span className="sr-only">ANALYSIS & RULES</span>
            </button>
            <button role="tab" aria-selected={activeTab === 'coach'} className={activeTab === 'coach' ? 'active' : ''} onClick={() => setActiveTab('coach')}>
              セットアップ <span className="sr-only">INST COACH</span>
            </button>
            <button role="tab" aria-selected={activeTab === 'strategy'} className={activeTab === 'strategy' ? 'active' : ''} onClick={() => setActiveTab('strategy')}>
              戦略 <span className="sr-only">STRATEGY GUIDE</span>
            </button>
            <button role="tab" aria-selected={activeTab === 'reviews'} className={activeTab === 'reviews' ? 'active' : ''} onClick={() => setActiveTab('reviews')}>
              レビュー <span className="sr-only">SUBAGENT REVIEWS</span>
            </button>
            <button role="tab" aria-selected={activeTab === 'graph'} className={activeTab === 'graph' ? 'active' : ''} onClick={() => setActiveTab('graph')}>
              関連ゲーム <span className="sr-only">CONNECTIONS</span>
            </button>
            {hasInfographics && (
              <button role="tab" aria-selected={activeTab === 'infographics'} className={activeTab === 'infographics' ? 'active' : ''} onClick={() => setActiveTab('infographics')}>
                図で見る <span className="sr-only">INFOGRAPHICS</span>
              </button>
            )}
          </div>

          <div className="pro-main-col">
            {activeTab === 'rules' && (
              <div className="markdown-content">
                <ReactMarkdown>{rules}</ReactMarkdown>
              </div>
            )}

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

            {activeTab === 'strategy' && (
              <div className="markdown-content">
                {sd.strategy_analysis ? (
                  <ReactMarkdown>{sd.strategy_analysis}</ReactMarkdown>
                ) : (
                  <div className="game-empty-state" role="status">
                    戦略解説はまだ登録されていません。必要に応じて再生成してください。
                  </div>
                )}
              </div>
            )}

            {activeTab === 'reviews' && (
              <div className="persona-reviews">
                <div className="pro-card-title">SUB-AGENT PERSPECTIVES</div>
                <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '1.5rem' }}>
                  異なるプレイスタイルのAIエージェントによる多角的な評価。
                </p>

                {sd.persona_reviews?.length > 0 ? sd.persona_reviews.map((rev, i) => (
                  <div key={i} className="review-card">
                    <div className="review-header">
                      <span className="persona-badge">{rev.persona}</span>
                      <span className="rating-badge">{rev.rating} / 10</span>
                    </div>
                    <div className="review-text">「{rev.review_text}」</div>
                  </div>
                )) : (
                  <div className="game-empty-state" role="status">
                    レビューはまだ登録されていません。必要に応じて再生成してください。
                  </div>
                )}
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

            {activeTab === 'infographics' && (
              <div style={{ display: 'grid', gap: '1rem' }}>
                {hasRuleFlow && <RuleFlowDiagram guide={ruleGuide} />}
                {legacyInfographicsVerified && (
                  <InfographicsGallery
                    infographics={game.infographics}
                    verified={legacyInfographicsVerified}
                    sourceUrl={legacyInfographicsSourceUrl}
                  />
                )}
              </div>
            )}

            {activeTab === 'data' && <pre className="game-data-dump">{JSON.stringify(game, null, 2)}</pre>}
          </div>
        </div>

        <div className="game-sidebar" aria-label="ゲーム基本情報">
          <div className="pro-stats-grid">
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
              <div className="pro-stat-value">{game.play_time != null ? `${game.play_time}m` : 'N/A'}</div>
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
            <div className="pro-card-title">30秒でわかる「{title}」</div>
            <div className="summary-text">{game.summary || game.description}</div>
          </div>

          <div className="pro-card" aria-label="データ信頼状態">
            <div className="pro-card-title">TRUST &amp; PROVENANCE</div>
            <div className="game-empty-note">{identityLabel}</div>
            <div className="game-empty-note">{sourceTrustLabel}</div>
            <div className="game-empty-note">{reviewLabel}</div>
          </div>

          {sd.pro_tips?.length > 0 && (
            <div className="pro-card">
              <div className="pro-card-title">💡 PRO TIPS</div>
              {sd.pro_tips.map((tip, i) => (
                <div key={i} className="tip-item">
                  <span className="tip-bullet">»</span>
                  <span>{tip}</span>
                </div>
              ))}
            </div>
          )}

          {sd.rule_mistakes?.length > 0 && (
            <div className="pro-card">
              <div className="pro-card-title">⚠️ COMMON ERRORS</div>
              {sd.rule_mistakes.map((err, i) => (
                <div key={i} className="mistake-item">{err}</div>
              ))}
            </div>
          )}

          <ConceptGlossary slug={slug} legacyKeywords={sd.keywords || []} />

          <div className="pro-card">
            <div className="pro-card-title">LINKS</div>
            <ExternalLinks game={game} />
          </div>
        </div>
      </div>
    </div>
  )
}
