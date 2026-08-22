import { useEffect, useMemo, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { Helmet } from 'react-helmet-async'
import { api } from '../lib/api'
import { ShareButton, TwitterShareButton } from '../components/game/ShareButtons'
import { TextToSpeech } from '../components/game/TextToSpeech'
import { ExternalLinks } from '../components/game/ExternalLinks'
import { RuleAskPanel } from '../components/game/RuleAskPanel'
import { ConceptGlossary } from '../components/game/ConceptGlossary'

const IDENTITY_LABELS = {
  verified: 'IDENTITY VERIFIED',
  needs_review: 'IDENTITY REVIEW REQUIRED',
  unverified: 'IDENTITY UNVERIFIED',
}

function ruleSetLabel(ruleSet) {
  if (!ruleSet) return 'RuleSet未選択'
  return [
    ruleSet.edition_label || ruleSet.variant_label || ruleSet.ruleset_id,
    ruleSet.platform,
    ruleSet.language_code,
    ruleSet.revision_label,
  ].filter(Boolean).join(' · ')
}

function availableItems(section) {
  return section?.status === 'available' ? section.items || [] : []
}

function RuleSection({ title, section }) {
  const items = availableItems(section)
  if (!items.length) return null
  return (
    <section className="pro-card" aria-label={title}>
      <div className="pro-card-title">{title}</div>
      <ol style={{ display: 'grid', gap: '0.65rem', paddingLeft: '1.25rem', margin: 0 }}>
        {items.map((item) => (
          <li key={item.rule_id}>
            <div>{item.text}</div>
            <div className="game-empty-note" style={{ marginTop: '3px' }}>
              Claim {item.evidence.claim_id} · Sources {item.evidence.source_ids.join(', ')}
            </div>
          </li>
        ))}
      </ol>
    </section>
  )
}

function CoachStep({ number, title, section }) {
  const items = availableItems(section)
  return (
    <div className={`coach-step${number === 1 ? ' active' : ''}`}>
      <span className="coach-step-num">STEP {number}</span>
      <div className="coach-step-title">{title}</div>
      {items.length ? (
        <ol style={{ fontSize: '0.95rem', lineHeight: 1.6, paddingLeft: '1.25rem' }}>
          {items.map((item) => <li key={item.rule_id}>{item.text}</li>)}
        </ol>
      ) : (
        <div className="game-empty-note">このsectionのaccepted evidence-backed ruleは未整備です。</div>
      )}
    </div>
  )
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
  const [ruleSets, setRuleSets] = useState([])
  const [selectedRuleSetId, setSelectedRuleSetId] = useState('')
  const [projection, setProjection] = useState(null)
  const [projectionStatus, setProjectionStatus] = useState('loading')

  const BASE_URL = 'https://bodoge-no-mikata.vercel.app'

  useEffect(() => {
    if (initialGame) return undefined
    let cancelled = false
    setLoading(true)
    setError(null)
    api.get(`/api/games/${slug}`)
      .then((data) => {
        if (cancelled) return
        const gameData = Array.isArray(data) ? data[0] : data.game || data
        setGame(gameData)
      })
      .catch((err) => {
        console.error(err)
        if (!cancelled) setError('ゲーム情報の取得に失敗しました')
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => { cancelled = true }
  }, [slug, initialGame])

  useEffect(() => {
    let cancelled = false
    setRuleSets([])
    setSelectedRuleSetId('')
    setProjection(null)
    setProjectionStatus('loading')

    api.get(`/api/games/${slug}/rule-sets`)
      .then((data) => {
        if (cancelled) return
        const rows = data?.status === 'available' ? data.rulesets || [] : []
        setRuleSets(rows)
        setSelectedRuleSetId(rows[0]?.ruleset_id || '')
        if (!rows.length) setProjectionStatus('not_available')
      })
      .catch(() => {
        if (!cancelled) setProjectionStatus('not_available')
      })

    return () => { cancelled = true }
  }, [slug])

  useEffect(() => {
    if (!selectedRuleSetId) return undefined
    let cancelled = false
    setProjection(null)
    setProjectionStatus('loading')
    const params = new URLSearchParams({ rule_set_id: selectedRuleSetId, language_code: 'ja' })
    api.get(`/api/games/${slug}/presentation?${params}`)
      .then((data) => {
        if (cancelled) return
        setProjection(data)
        setProjectionStatus(data?.status === 'available' ? 'available' : 'not_available')
      })
      .catch(() => {
        if (!cancelled) setProjectionStatus('not_available')
      })
    return () => { cancelled = true }
  }, [slug, selectedRuleSetId])

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

  const selectedRuleSet = useMemo(
    () => ruleSets.find((row) => row.ruleset_id === selectedRuleSetId) || null,
    [ruleSets, selectedRuleSetId],
  )
  const hasCoach = Boolean(
    availableItems(projection?.setup).length ||
    availableItems(projection?.game_flow).length ||
    availableItems(projection?.end_condition).length,
  )
  const speechText = availableItems(projection?.quick_rules).map((item) => item.text).join(' ')

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
  const identityLabel = IDENTITY_LABELS[game.identity_status] || IDENTITY_LABELS.unverified
  const pageTitle = `「${title}」のルール・出典 | ボドゲのミカタ`
  const description = game.summary || game.description || `「${title}」の登録情報と出典を確認できます。`
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
          <TextToSpeech text={`${title}. ${speechText || description}`} />
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
                  ? game.max_players != null
                    ? `${game.min_players}${game.max_players !== game.min_players ? `-${game.max_players}` : ''}`
                    : `${game.min_players}+`
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
            <div className="pro-card-title">「{title}」のゲーム概要</div>
            <div className="summary-text">{description}</div>
          </div>

          <section className="pro-card" aria-label="RuleSet selector">
            <div className="pro-card-title">RULESET</div>
            {ruleSets.length ? (
              <>
                {ruleSets.length > 1 ? (
                  <label>
                    <span className="sr-only">表示するルール版</span>
                    <select
                      value={selectedRuleSetId}
                      onChange={(event) => {
                        setSelectedRuleSetId(event.target.value)
                        setActiveTab('rules')
                      }}
                    >
                      {ruleSets.map((row) => (
                        <option key={row.ruleset_id} value={row.ruleset_id}>{ruleSetLabel(row)}</option>
                      ))}
                    </select>
                  </label>
                ) : (
                  <div>{ruleSetLabel(selectedRuleSet)}</div>
                )}
                <div className="game-empty-note" style={{ marginTop: '0.5rem' }}>
                  verification: {selectedRuleSet?.verification_status || 'unknown'}
                  {selectedRuleSet?.source_ids?.length ? ` · sources: ${selectedRuleSet.source_ids.join(', ')}` : ''}
                </div>
              </>
            ) : (
              <div className="game-empty-state" role="status">
                正準RuleSetはまだ登録されていません。旧ゲーム行のルール本文へfallbackしません。
              </div>
            )}
          </section>

          <RuleAskPanel projection={projection} ruleSet={selectedRuleSet} />

          <div className="rules-tabs" role="group" aria-label="ゲーム詳細表示">
            <button type="button" aria-pressed={activeTab === 'rules'} className={activeTab === 'rules' ? 'active' : ''} onClick={() => setActiveTab('rules')}>
              詳しいルール
            </button>
            {hasCoach && (
              <button type="button" aria-pressed={activeTab === 'coach'} className={activeTab === 'coach' ? 'active' : ''} onClick={() => setActiveTab('coach')}>
                準備・流れ・終了
              </button>
            )}
            <button type="button" aria-pressed={activeTab === 'graph'} className={activeTab === 'graph' ? 'active' : ''} onClick={() => setActiveTab('graph')}>
              関連ゲーム
            </button>
          </div>

          <div className="pro-main-col">
            {activeTab === 'rules' && (
              <div style={{ display: 'grid', gap: '1rem' }}>
                {projectionStatus === 'loading' && (
                  <div className="game-empty-state" role="status">正準ルールを照合しています...</div>
                )}
                {projectionStatus === 'not_available' && (
                  <div className="game-empty-state" role="status">
                    選択中RuleSetにはaccepted evidence-backed presentationがまだありません。
                  </div>
                )}
                {projectionStatus === 'available' && (
                  <>
                    <RuleSection title="QUICK RULES" section={projection.quick_rules} />
                    <RuleSection title="SETUP" section={projection.setup} />
                    <RuleSection title="GAME FLOW" section={projection.game_flow} />
                    <RuleSection title="END CONDITION" section={projection.end_condition} />
                    <RuleSection title="SCORING" section={projection.scoring} />
                  </>
                )}
              </div>
            )}

            {activeTab === 'coach' && (
              <div className="coach-mode">
                <CoachStep number={1} title="セットアップ" section={projection?.setup} />
                <CoachStep number={2} title="ゲームの流れ" section={projection?.game_flow} />
                <CoachStep number={3} title="ゲーム終了" section={projection?.end_condition} />
                <div style={{ textAlign: 'center', padding: '1rem', color: 'var(--text-muted)', fontSize: '0.8rem' }}>
                  選択中RuleSetのaccepted evidence-backed RuleNodeだけを表示しています。
                </div>
              </div>
            )}

            {activeTab === 'graph' && (
              <div className="graph-perspective">
                <div className="pro-card-title">CONNECTIONS (MECHANICAL DNA v2)</div>
                <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '1.5rem' }}>
                  正準Concept IDの共有関係から、説明可能な関連ゲームを算出します。
                </p>
                {connectionsLoading && <div className="game-empty-state" role="status">関連ゲームを照合しています...</div>}
                {!connectionsLoading && connectionsError && (
                  <div className="game-empty-state" role="status">関連ゲームの正準データを取得できませんでした。</div>
                )}
                {!connectionsLoading && !connectionsError && connections?.status === 'not_available' && (
                  <div className="game-empty-state" role="status">関連ゲームの正準データは未整備です。</div>
                )}
                {!connectionsLoading && !connectionsError && connections?.status === 'available' && connections.connections?.length === 0 && (
                  <div className="game-empty-state" role="status">正準Concept上の関連ゲームはまだ登録されていません。</div>
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
                    </div>
                  </Link>
                ))}
              </div>
            )}
          </div>
        </div>

        <div className="game-sidebar" aria-label="補足情報">
          <div className="pro-card" aria-label="データ信頼状態">
            <div className="pro-card-title">TRUST &amp; PROVENANCE</div>
            <div className="game-empty-note">{identityLabel}</div>
            <div className="game-empty-note">
              RULESET {selectedRuleSet?.verification_status?.toUpperCase() || 'NOT AVAILABLE'}
            </div>
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
