import { useEffect, useState, useMemo } from 'react'
import { useSearchParams, Link, useNavigate } from 'react-router-dom'
import { api } from './lib/api'

function App() {
  const [searchParams, setSearchParams] = useSearchParams()
  const navigate = useNavigate()
  
  const [initialGames, setInitialGames] = useState([])
  const [totalGamesCount, setTotalGamesCount] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [generating, setGenerating] = useState(false)

  // Filters state
  const [query, setQuery] = useState(searchParams.get('q') || '')
  const [activePlayers, setActivePlayers] = useState(null)
  const [activeTime, setActiveTime] = useState(null)
  const [activeTier, setActiveTier] = useState(null)
  const [sortOption, setSortOption] = useState('recent')

  // Comparison State
  const [compareList, setCompareList] = useState([])
  const [isBattleMode, setIsBattleMode] = useState(false)

  const loadAllGames = async () => {
    setError(null)
    setLoading(true)
    try {
      const data = await api.get(`/api/games?limit=20000&offset=0`)
      const list = data.games || []
      const total = data.total || 0

      setInitialGames(list)
      setTotalGamesCount(total)
    } catch (err) {
      console.error('Failed to load games:', err)
      setError('ゲームの読み込みに失敗しました。')
    } finally {
      setLoading(false)
    }
  }

  const handleLoadMore = async () => {
    if (initialGames.length >= totalGamesCount) return
    setLoading(true)
    try {
      const data = await api.get(`/api/games?limit=1000&offset=${initialGames.length}`)
      const newGames = data.games || []
      setInitialGames([...initialGames, ...newGames])
    } catch (err) {
      console.error('Failed to load more games:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadAllGames()
  }, [])

  // Derived unique values
  const availableTiers = useMemo(() => {
    const tiers = new Set(initialGames.map(g => g.strategy_tier).filter(Boolean))
    return Array.from(tiers).sort()
  }, [initialGames])

  // Filtering Logic
  const filteredGames = useMemo(() => {
    let result = [...initialGames]

    // Search Query
    if (query) {
      const q = query.trim().normalize('NFKC').toLowerCase()
      result = result.filter((game) => {
        const title = (game.title || '').normalize('NFKC').toLowerCase()
        const titleJa = (game.title_ja || '').normalize('NFKC').toLowerCase()
        const titleEn = (game.title_en || '').normalize('NFKC').toLowerCase()
        const summary = (game.summary || '').normalize('NFKC').toLowerCase()
        return title.includes(q) || titleJa.includes(q) || titleEn.includes(q) || summary.includes(q)
      })
    }

    // Player Count Filter
    if (activePlayers) {
      const p = parseInt(activePlayers)
      result = result.filter(g => {
        const min = g.min_players || 1
        const max = g.max_players || 99
        if (activePlayers === '5+') return max >= 5
        return p >= min && p <= max
      })
    }

    // Play Time Filter
    if (activeTime) {
      result = result.filter(g => {
        const t = g.play_time || 0
        if (activeTime === '30-') return t > 0 && t <= 30
        if (activeTime === '30-60') return t > 30 && t <= 60
        if (activeTime === '60-120') return t > 60 && t <= 120
        if (activeTime === '120+') return t > 120
        return true
      })
    }

    // Tier Filter
    if (activeTier) {
      result = result.filter(g => g.strategy_tier === activeTier)
    }

    // Sorting
    result.sort((a, b) => {
      if (sortOption === 'recent') {
        const dateA = a.created_at ? new Date(a.created_at).getTime() : 0
        const dateB = b.created_at ? new Date(b.created_at).getTime() : 0
        return dateB - dateA
      }
      if (sortOption === 'title') {
        const ta = a.title_ja || a.title || ''
        const tb = b.title_ja || b.title || ''
        return ta.localeCompare(tb)
      }
      if (sortOption === 'year') {
        const ya = a.published_year || 0
        const yb = b.published_year || 0
        return yb - ya
      }
      if (sortOption === 'play_time') {
        const ta = a.play_time || 0
        const tb = b.play_time || 0
        return ta - tb
      }
      return 0
    })

    return result
  }, [initialGames, query, activePlayers, activeTime, activeTier, sortOption])

  // Sync Search Query to URL
  useEffect(() => {
    const timer = setTimeout(() => {
      if (query) {
        setSearchParams({ q: query }, { replace: true })
      } else {
        setSearchParams({}, { replace: true })
      }
    }, 300)
    return () => clearTimeout(timer)
  }, [query, setSearchParams])

  const handleSearchSubmit = async (e) => {
    e.preventDefault()
    if (!query.trim()) return

    setGenerating(true)
    setError(null)
    try {
      const data = await api.post('/api/search', { query, generate: true })
      const list = Array.isArray(data) ? data : data.games || []
      if (list.length > 0) {
        const newGame = list[0]
        const exists = initialGames.find((g) => g.slug === newGame.slug)
        if (!exists) {
          setInitialGames([newGame, ...initialGames])
        }
        navigate(`/games/${newGame.slug}`)
      }
    } catch (e) {
      console.error(e)
      setError('AI生成リクエストに失敗しました。')
    } finally {
      setGenerating(false)
    }
  }

  const clearFilters = () => {
    setQuery('')
    setActivePlayers(null)
    setActiveTime(null)
    setActiveTier(null)
  }

  const toggleCompare = (game) => {
    if (compareList.find(g => g.id === game.id)) {
      setCompareList(compareList.filter(g => g.id !== game.id))
    } else {
      if (compareList.length >= 3) return
      setCompareList([...compareList, game])
    }
  }

  if (isBattleMode) {
    return (
      <div className="game-detail-content" style={{ overflowY: 'auto', height: '100dvh', padding: '2rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
          <h1 className="game-title">COMPARISON BATTLE</h1>
          <button className="filter-btn" style={{ borderColor: '#fff' }} onClick={() => setIsBattleMode(false)}>CLOSE BATTLE</button>
        </div>
        
        <div className="battle-grid">
          {compareList.map(game => (
            <div key={game.id} className="battle-col">
              <div className="pro-card" style={{ textAlign: 'center' }}>
                <img src={game.image_url || '/assets/no-image.webp'} style={{ width: '100%', borderRadius: '8px', marginBottom: '1rem' }} alt={game.title_ja} />
                <div className="pro-stat-value">{game.title_ja || game.title}</div>
                {game.strategy_tier && <div className="tier-badge" style={{ position: 'static', marginTop: '8px' }}>TIER {game.strategy_tier}</div>}
              </div>

              <div className="battle-attr">
                <div className="battle-attr-label">Synopsis</div>
                <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>{game.summary || 'No summary available.'}</div>
              </div>

              <div className="battle-attr">
                <div className="battle-attr-label">Specs</div>
                <div className="pro-stats-grid" style={{ marginBottom: 0 }}>
                  <div className="pro-stat-card"><div className="pro-stat-label">P</div><div className="pro-stat-value" style={{ fontSize: '0.9rem' }}>{game.min_players}-{game.max_players}</div></div>
                  <div className="pro-stat-card"><div className="pro-stat-label">T</div><div className="pro-stat-value" style={{ fontSize: '0.9rem' }}>{game.play_time}m</div></div>
                </div>
              </div>

              {game.structured_data?.mechanics && (
                <div className="battle-attr">
                  <div className="battle-attr-label">Mechanics</div>
                  <div className="tag-list">
                    {game.structured_data.mechanics.slice(0, 5).map(m => <span key={m} className="tag-item">{m}</span>)}
                  </div>
                </div>
              )}
              
              <div style={{ marginTop: '2rem' }}>
                <Link to={`/games/${game.slug}`} className="filter-btn" style={{ width: '100%', display: 'block', textDecoration: 'none' }}>VIEW FULL ANALYSIS</Link>
              </div>
            </div>
          ))}
        </div>
      </div>
    )
  }

  return (
    <>
      <header>
        <Link to="/" className="logo">
          <div className="logo-text">ボドゲのミカタ</div>
        </Link>
        
        <form className="search-container" onSubmit={handleSearchSubmit}>
          <input 
            type="text" 
            className="search-input" 
            placeholder="ゲームを検索、または未登録ゲームをAI生成..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
        </form>

        <div className="db-status">
          <div className="status-dot connected"></div>
          {loading ? 'SYNCING...' : `${totalGamesCount} GAMES`}
        </div>
      </header>

      <aside>
        <div className="filter-section">
          <h3>プレイ人数</h3>
          <div className="filter-grid">
            {['1', '2', '3', '4', '5+'].map(p => (
              <button 
                key={p} 
                className={`filter-btn ${activePlayers === p ? 'active' : ''}`}
                onClick={() => setActivePlayers(activePlayers === p ? null : p)}
              >
                {p}人
              </button>
            ))}
          </div>
        </div>

        <div className="filter-section">
          <h3>プレイ時間</h3>
          <div className="filter-grid" style={{ gridTemplateColumns: '1fr' }}>
            {[
              { id: '30-', label: '30分以内' },
              { id: '30-60', label: '30-60分' },
              { id: '60-120', label: '60-120分' },
              { id: '120+', label: '120分以上' }
            ].map(t => (
              <button 
                key={t.id} 
                className={`filter-btn ${activeTime === t.id ? 'active' : ''}`}
                onClick={() => setActiveTime(activeTime === t.id ? null : t.id)}
              >
                {t.label}
              </button>
            ))}
          </div>
        </div>

        {availableTiers.length > 0 && (
          <div className="filter-section">
            <h3>戦略ティア</h3>
            <div className="filter-grid">
              {availableTiers.map(t => (
                <button 
                  key={t} 
                  className={`filter-btn ${activeTier === t ? 'active' : ''}`}
                  onClick={() => setActiveTier(activeTier === t ? null : t)}
                >
                  Tier {t}
                </button>
              ))}
            </div>
          </div>
        )}

        <div className="filter-section">
          <button 
            className="filter-btn" 
            style={{ width: '100%', borderColor: 'var(--accent-secondary)' }}
            onClick={clearFilters}
          >
            フィルターをリセット
          </button>
        </div>
      </aside>

      <main>
        <div className="control-panel">
          <div className="active-filters" style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: '700' }}>
              {filteredGames.length} RESULTS
            </span>
            {activePlayers && <div className="filter-chip">人数: {activePlayers} <button onClick={() => setActivePlayers(null)}>×</button></div>}
            {activeTime && <div className="filter-chip">時間: {activeTime} <button onClick={() => setActiveTime(null)}>×</button></div>}
            {activeTier && <div className="filter-chip">Tier: {activeTier} <button onClick={() => setActiveTier(null)}>×</button></div>}
          </div>
          
          <select 
            className="sort-select" 
            value={sortOption} 
            onChange={(e) => setSortOption(e.target.value)}
          >
            <option value="recent">最近追加</option>
            <option value="title">タイトル順</option>
            <option value="year">発売年順</option>
            <option value="play_time">プレイ時間順</option>
          </select>
        </div>

        {error && <div style={{ color: '#ff4444', padding: '1rem', background: '#2a0000', borderRadius: '8px' }}>{error}</div>}
        {generating && <div style={{ padding: '1rem', background: '#1a1a1a', borderRadius: '8px', border: '1px solid #444', color: '#aaa', textAlign: 'center' }}>AIが新しいゲーム情報を生成しています...</div>}

        {loading ? (
          <div style={{ textAlign: 'center', padding: '2rem', color: '#666' }}>ARCHIVE INITIALIZING...</div>
        ) : (
          <div className="asset-grid">
            {filteredGames.map(game => (
              <div key={game.id} style={{ position: 'relative' }}>
                <Link to={`/games/${game.slug}`} className="asset-card" style={{ height: '100%' }}>
                  <div className="asset-thumb-container">
                    {game.strategy_tier && <div className="tier-badge">Tier {game.strategy_tier}</div>}
                    <img 
                      src={game.image_url || '/assets/no-image.webp'} 
                      alt={game.title_ja || game.title} 
                      className="asset-thumb"
                      loading="lazy"
                    />
                  </div>
                  <div className="asset-info">
                    <div className="asset-title">{game.title_ja || game.title}</div>
                    <div className="asset-meta">
                      {game.min_players && <span className="meta-item">👥 {game.min_players}{game.max_players && game.max_players !== game.min_players ? `-${game.max_players}` : ''}</span>}
                      {game.play_time && <span className="meta-item">⏳ {game.play_time}m</span>}
                      {game.published_year && <span className="meta-item">📅 {game.published_year}</span>}
                    </div>
                    <div className="asset-summary">{game.summary || game.description}</div>
                  </div>
                </Link>
                <button 
                  onClick={(e) => { e.preventDefault(); toggleCompare(game); }}
                  className={`filter-btn ${compareList.find(g => g.id === game.id) ? 'active' : ''}`}
                  style={{ position: 'absolute', top: '8px', right: '8px', zIndex: 10, padding: '4px 8px', fontSize: '0.65rem' }}
                >
                  {compareList.find(g => g.id === game.id) ? 'READY' : 'COMPARE'}
                </button>
              </div>
            ))}
            {filteredGames.length === 0 && !loading && (
              <div style={{ gridColumn: '1 / -1', textAlign: 'center', padding: '3rem', color: '#666' }}>
                条件に一致するゲームが見つかりません。
              </div>
            )}
          </div>
        )}
        
        {!loading && initialGames.length < totalGamesCount && (
          <div style={{ textAlign: 'center', padding: '2rem' }}>
            <button 
              className="filter-btn" 
              style={{ padding: '10px 24px', fontSize: '0.9rem', borderColor: 'var(--accent)' }}
              onClick={handleLoadMore}
            >
              さらに読み込む ({initialGames.length} / {totalGamesCount})
            </button>
          </div>
        )}
      </main>

      {compareList.length > 0 && (
        <div className="comparison-tray">
          <div style={{ fontSize: '0.75rem', fontWeight: 700, color: '#666' }}>BATTLE TRAY</div>
          {compareList.map(g => (
            <div key={g.id} className="compare-item">
              <img src={g.image_url || '/assets/no-image.webp'} style={{ width: '100%', height: '100%', objectFit: 'cover' }} alt="Compare Item" />
              <button onClick={() => toggleCompare(g)}>×</button>
            </div>
          ))}
          {compareList.length >= 2 && (
            <button 
              className="filter-btn active" 
              style={{ padding: '6px 16px', borderRadius: '20px' }}
              onClick={() => setIsBattleMode(true)}
            >
              BATTLE START
            </button>
          )}
        </div>
      )}
    </>
  )
}

export default App
