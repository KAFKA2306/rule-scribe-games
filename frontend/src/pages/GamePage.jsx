import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { Helmet } from 'react-helmet-async'
import ReactMarkdown from 'react-markdown'
import { api } from '../lib/api'
import { ShareButton, TwitterShareButton } from '../components/game/ShareButtons'
import { RegenerateButton } from '../components/game/RegenerateButton'
import { TextToSpeech } from '../components/game/TextToSpeech'
import { ExternalLinks } from '../components/game/ExternalLinks'
import { InfographicsGallery } from '../components/game/InfographicsGallery'

export default function GamePage({ slug: propSlug, initialGame, allGames: propAllGames }) {
  const { slug: urlSlug } = useParams()
  const slug = propSlug || urlSlug

  const [game, setGame] = useState(initialGame || null)
  const [allGames, setAllGames] = useState(propAllGames || [])
  const [loading, setLoading] = useState(!initialGame)
  const [error, setError] = useState(null)
  const [activeTab, setActiveTab] = useState('rules')

  const BASE_URL = 'https://rule-scribe-games.vercel.app'

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
      
      if (allGames.length === 0) {
        try {
          const data = await api.get('/api/games?limit=50')
          setAllGames(data.games || [])
        } catch (err) {
          console.error('Failed to fetch connections:', err)
        }
      }
    }
    fetchData()
  }, [slug, initialGame, allGames.length])

  if (loading) return <div style={{ padding: '4rem', textAlign: 'center', color: '#666' }}>ARCHIVE LOADING...</div>

  if (error || !game) {
    return (
      <div style={{ padding: '4rem', textAlign: 'center' }}>
        <p>{error || 'Game not found'}</p>
        <Link to="/" className="back-link">ディレクトリに戻る</Link>
      </div>
    )
  }

  const title = game.title_ja || game.title || 'Untitled'
  const rules = game.rules_content || ''
  const sd = game.structured_data || {}

  const pageTitle = `「${title}」のルール・戦略・インスト要約 | ボドゲのミカタ`
  const description = game.summary || `「${title}」のルールをAIが瞬時に分析。セットアップから勝利戦略まで。`
  const gameUrl = `${BASE_URL}/games/${slug}`
  const imageUrl = game.image_url || `${BASE_URL}/assets/no-image.webp`

  return (
    <div className="game-detail-content" style={{ overflowY: 'auto', height: '100dvh', padding: '1.5rem 2rem' }}>
      <Helmet>
        <title>{pageTitle}</title>
        <meta name="description" content={description} />
      </Helmet>

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <Link to="/" className="back-link" style={{ margin: 0 }}>← DIRECTORY</Link>
        <div className="header-actions">
          <TextToSpeech text={`${title}. ${description}`} />
          <TwitterShareButton slug={slug} title={title} />
          <ShareButton slug={slug} />
          <RegenerateButton title={title} onRegenerate={setGame} />
        </div>
      </div>

      <div className="game-content">
        <h1 className="game-title">{title}</h1>
        {game.strategy_tier && <div className="tier-badge" style={{ position: 'static', fontSize: '1.2rem', padding: '4px 12px' }}>TIER {game.strategy_tier}</div>}
      </div>

      <div className="pro-stats-grid">
        <div className="pro-stat-card">
          <div className="pro-stat-label">PLAYERS</div>
          <div className="pro-stat-value">{game.min_players}{game.max_players ? `-${game.max_players}` : ''}</div>
        </div>
        <div className="pro-stat-card">
          <div className="pro-stat-label">TIME</div>
          <div className="pro-stat-value">{game.play_time}m</div>
        </div>
        <div className="pro-stat-card">
          <div className="pro-stat-label">AGE</div>
          <div className="pro-stat-value">{game.min_age}+</div>
        </div>
        <div className="pro-stat-card">
          <div className="pro-stat-label">YEAR</div>
          <div className="pro-stat-value">{game.published_year || 'N/A'}</div>
        </div>
      </div>

      <div className="pro-card" style={{ borderLeft: '4px solid #fff' }}>
        <div className="pro-card-title">SYNOPSIS</div>
        <div className="summary-text">{game.summary || game.description}</div>
      </div>

      <div className="rules-tabs">
        <button className={activeTab === 'rules' ? 'active' : ''} onClick={() => setActiveTab('rules')}>ANALYSIS & RULES</button>
        <button className={activeTab === 'coach' ? 'active' : ''} onClick={() => setActiveTab('coach')}>INST COACH</button>
        <button className={activeTab === 'strategy' ? 'active' : ''} onClick={() => setActiveTab('strategy')}>STRATEGY GUIDE</button>
        <button className={activeTab === 'reviews' ? 'active' : ''} onClick={() => setActiveTab('reviews')}>SUBAGENT REVIEWS</button>
        <button className={activeTab === 'graph' ? 'active' : ''} onClick={() => setActiveTab('graph')}>CONNECTIONS</button>
        {game.infographics && <button className={activeTab === 'infographics' ? 'active' : ''} onClick={() => setActiveTab('infographics')}>INFOGRAPHICS</button>}
      </div>

      <div className="pro-section-grid">
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
                <div className="coach-step-title">セットアップ (Setup)</div>
                <div style={{ fontSize: '0.95rem', lineHeight: 1.6 }}>
                  コンポーネントを準備し、各プレイヤーに初期リソースを配布します。
                  {sd.key_elements?.length > 0 && (
                    <div style={{ marginTop: '1rem', color: 'var(--text-secondary)' }}>
                      💡 注目要素: {sd.key_elements.map(e => e.name).join(', ')}
                    </div>
                  )}
                </div>
              </div>

              <div className="coach-step">
                <span className="coach-step-num">STEP 2</span>
                <div className="coach-step-title">ゲームの目的 (Objective)</div>
                <div style={{ fontSize: '0.95rem', lineHeight: 1.6 }}>
                  {game.summary || '勝利条件を確認します。'}
                </div>
              </div>

              <div className="coach-step">
                <span className="coach-step-num">STEP 3</span>
                <div className="coach-step-title">手番の流れ (Turn Flow)</div>
                <div style={{ fontSize: '0.95rem', lineHeight: 1.6 }}>
                  1. アクションを選択 <br />
                  2. リソースを支払う <br />
                  3. 効果を解決 <br />
                  <br />
                  {sd.mechanics?.length > 0 && (
                    <div className="tag-list">
                      {sd.mechanics.map(m => <span key={m} className="tag-item">{m}</span>)}
                    </div>
                  )}
                </div>
              </div>
              
              <div style={{ textAlign: 'center', padding: '1rem', color: 'var(--text-muted)', fontSize: '0.8rem' }}>
                AIによるインストガイドです。詳細は「ANALYSIS & RULES」タブを確認してください。
              </div>
            </div>
          )}

          {activeTab === 'strategy' && (
            <div className="markdown-content">
              {sd.strategy_analysis ? (
                <ReactMarkdown>{sd.strategy_analysis}</ReactMarkdown>
              ) : (
                <div style={{ padding: '2rem', textAlign: 'center', background: '#111', borderRadius: '8px', color: '#666' }}>
                  No deep strategy analysis available yet. Try regenerating.
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
                <div style={{ padding: '2rem', textAlign: 'center', background: '#111', borderRadius: '8px', color: '#666' }}>
                  No persona reviews available yet. Try regenerating.
                </div>
              )}
            </div>
          )}

          {activeTab === 'graph' && (
            <div className="graph-perspective">
              <div className="pro-card-title">CONNECTIONS (MECHANICAL DNA)</div>
              <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '1.5rem' }}>
                このゲームと同じメカニクスを持つアーカイブ内のゲーム。
              </p>
              
              {sd.mechanics?.map((m, i) => {
                const related = allGames.filter(g => 
                  g.slug !== slug && 
                  g.structured_data?.mechanics?.includes(m)
                ).slice(0, 3)

                return (
                  <div key={i} style={{ marginBottom: '1.5rem' }}>
                    <div style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--accent)', marginBottom: '8px' }}>{m.toUpperCase()}</div>
                    {related.length > 0 ? related.map(rg => (
                      <Link to={`/games/${rg.slug}`} key={rg.id} className="relation-node">
                        <img src={rg.image_url || '/assets/no-image.webp'} style={{ width: '40px', height: '40px', objectFit: 'cover', borderRadius: '4px' }} alt={rg.title_ja} />
                        <div>
                          <div style={{ fontSize: '0.9rem', fontWeight: 600 }}>{rg.title_ja || rg.title}</div>
                          <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>{rg.summary?.slice(0, 40)}...</div>
                        </div>
                      </Link>
                    )) : (
                      <div style={{ fontSize: '0.8rem', color: '#444', padding: '10px' }}>No direct connections found in archive.</div>
                    )}
                  </div>
                )
              })}
            </div>
          )}

          {activeTab === 'infographics' && <InfographicsGallery infographics={game.infographics} />}
          {activeTab === 'data' && <pre style={{ background: '#111', padding: '1rem', borderRadius: '8px', overflowX: 'auto' }}>{JSON.stringify(game, null, 2)}</pre>}
        </div>

        <div className="pro-sidebar">
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

          {sd.keywords?.length > 0 && (
            <div className="pro-card">
              <div className="pro-card-title">GLOSSARY</div>
              <div className="tag-list">
                {sd.keywords.map((kw, i) => (
                  <div key={i} className="tag-item" title={kw.description}>{kw.term}</div>
                ))}
              </div>
            </div>
          )}

          <div className="pro-card">
            <div className="pro-card-title">LINKS</div>
            <ExternalLinks game={game} />
          </div>
        </div>
      </div>
    </div>
  )
}
