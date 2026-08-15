import { useEffect, useMemo, useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { api } from './lib/api'

const PLAYER_FILTERS = ['1', '2', '3', '4', '5+']
const TIME_FILTERS = [
  { id: '30-', label: '30分以内' },
  { id: '30-60', label: '30-60分' },
  { id: '60-120', label: '60-120分' },
  { id: '120+', label: '120分以上' },
]
const NO_IMAGE_URL = '/assets/no-image.webp'

function gameImageUrl(game) {
  const configured = game.image_url?.trim()
  if (configured && !configured.includes('placeholder') && !configured.endsWith(NO_IMAGE_URL)) return configured
  return game.slug ? `/images/games/generated/${game.slug}.webp` : NO_IMAGE_URL
}

function handleGameImageError(event) {
  if (!event.currentTarget.src.endsWith(NO_IMAGE_URL)) event.currentTarget.src = NO_IMAGE_URL
}

function Filters({
  activePlayers,
  activeTime,
  activeTier,
  availableTiers,
  setActivePlayers,
  setActiveTime,
  setActiveTier,
  clearFilters,
}) {
  return (
    <>
      <div className="filter-section">
        <h3>プレイ人数</h3>
        <div className="filter-grid">
          {PLAYER_FILTERS.map((player) => (
            <button
              key={player}
              type="button"
              className={`filter-btn ${activePlayers === player ? 'active' : ''}`}
              aria-pressed={activePlayers === player}
              onClick={() => setActivePlayers(activePlayers === player ? null : player)}
            >
              {player}人
            </button>
          ))}
        </div>
      </div>

      <div className="filter-section">
        <h3>プレイ時間</h3>
        <div className="filter-grid filter-grid--single">
          {TIME_FILTERS.map((time) => (
            <button
              key={time.id}
              type="button"
              className={`filter-btn ${activeTime === time.id ? 'active' : ''}`}
              aria-pressed={activeTime === time.id}
              onClick={() => setActiveTime(activeTime === time.id ? null : time.id)}
            >
              {time.label}
            </button>
          ))}
        </div>
      </div>

      {availableTiers.length > 0 && (
        <div className="filter-section">
          <h3>戦略ティア</h3>
          <div className="filter-grid">
            {availableTiers.map((tier) => (
              <button
                key={tier}
                type="button"
                className={`filter-btn ${activeTier === tier ? 'active' : ''}`}
                aria-pressed={activeTier === tier}
                onClick={() => setActiveTier(activeTier === tier ? null : tier)}
              >
                Tier {tier}
              </button>
            ))}
          </div>
        </div>
      )}

      <div className="filter-section">
        <button type="button" className="filter-btn filter-reset-button" onClick={clearFilters}>
          フィルターをリセット
        </button>
      </div>
    </>
  )
}

function App() {
  const [searchParams, setSearchParams] = useSearchParams()
  const navigate = useNavigate()

  const [initialGames, setInitialGames] = useState([])
  const [totalGamesCount, setTotalGamesCount] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [generating, setGenerating] = useState(false)

  const [query, setQuery] = useState(searchParams.get('q') || '')
  const [activePlayers, setActivePlayers] = useState(null)
  const [activeTime, setActiveTime] = useState(null)
  const [activeTier, setActiveTier] = useState(null)
  const [sortOption, setSortOption] = useState('recent')
  const [mobileFiltersOpen, setMobileFiltersOpen] = useState(false)

  const [compareList, setCompareList] = useState([])
  const [compareNotice, setCompareNotice] = useState('')
  const [isBattleMode, setIsBattleMode] = useState(false)

  const loadAllGames = async () => {
    setError(null)
    setLoading(true)
    try {
      const data = await api.get('/api/games?limit=20000&offset=0')
      setInitialGames(data.games || [])
      setTotalGamesCount(data.total || 0)
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
      setInitialGames((current) => [...current, ...newGames])
    } catch (err) {
      console.error('Failed to load more games:', err)
      setError('追加ゲームの読み込みに失敗しました。')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadAllGames()
  }, [])

  useEffect(() => {
    if (!mobileFiltersOpen) return undefined
    const onKeyDown = (event) => {
      if (event.key === 'Escape') setMobileFiltersOpen(false)
    }
    window.addEventListener('keydown', onKeyDown)
    return () => window.removeEventListener('keydown', onKeyDown)
  }, [mobileFiltersOpen])

  const availableTiers = useMemo(() => {
    const tiers = new Set(initialGames.map((game) => game.strategy_tier).filter(Boolean))
    return Array.from(tiers).sort()
  }, [initialGames])

  const filteredGames = useMemo(() => {
    let result = [...initialGames]

    if (query) {
      const normalized = query.trim().normalize('NFKC').toLowerCase()
      result = result.filter((game) => {
        const title = (game.title || '').normalize('NFKC').toLowerCase()
        const titleJa = (game.title_ja || '').normalize('NFKC').toLowerCase()
        const titleEn = (game.title_en || '').normalize('NFKC').toLowerCase()
        const summary = (game.summary || '').normalize('NFKC').toLowerCase()
        return title.includes(normalized) || titleJa.includes(normalized) || titleEn.includes(normalized) || summary.includes(normalized)
      })
    }

    if (activePlayers) {
      const playerCount = Number.parseInt(activePlayers, 10)
      result = result.filter((game) => {
        const min = game.min_players || 1
        const max = game.max_players || 99
        if (activePlayers === '5+') return max >= 5
        return playerCount >= min && playerCount <= max
      })
    }

    if (activeTime) {
      result = result.filter((game) => {
        const time = game.play_time || 0
        if (activeTime === '30-') return time > 0 && time <= 30
        if (activeTime === '30-60') return time > 30 && time <= 60
        if (activeTime === '60-120') return time > 60 && time <= 120
        if (activeTime === '120+') return time > 120
        return true
      })
    }

    if (activeTier) result = result.filter((game) => game.strategy_tier === activeTier)

    result.sort((a, b) => {
      if (sortOption === 'recent') {
        return (b.created_at ? new Date(b.created_at).getTime() : 0) - (a.created_at ? new Date(a.created_at).getTime() : 0)
      }
      if (sortOption === 'title') return (a.title_ja || a.title || '').localeCompare(b.title_ja || b.title || '')
      if (sortOption === 'year') return (b.published_year || 0) - (a.published_year || 0)
      if (sortOption === 'play_time') return (a.play_time || 0) - (b.play_time || 0)
      return 0
    })

    return result
  }, [initialGames, query, activePlayers, activeTime, activeTier, sortOption])

  useEffect(() => {
    const timer = window.setTimeout(() => {
      if (query) setSearchParams({ q: query }, { replace: true })
      else setSearchParams({}, { replace: true })
    }, 300)
    return () => window.clearTimeout(timer)
  }, [query, setSearchParams])

  const handleDirectorySearch = (event) => {
    event.preventDefault()
    // Filtering is intentionally local. AI generation is a separate explicit action.
  }

  const handleGenerateGame = async () => {
    const normalized = query.trim()
    if (!normalized || generating) return

    setGenerating(true)
    setError(null)
    try {
      const data = await api.post('/api/search', { query: normalized, generate: true })
      const list = Array.isArray(data) ? data : data.games || []
      if (list.length === 0) {
        setError('未登録ゲームを生成できませんでした。名称を確認してください。')
        return
      }

      const newGame = list[0]
      setInitialGames((current) => current.some((game) => game.slug === newGame.slug) ? current : [newGame, ...current])
      navigate(`/games/${newGame.slug}`)
    } catch (err) {
      console.error(err)
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
    const selected = compareList.some((candidate) => candidate.id === game.id)
    if (selected) {
      setCompareList((current) => current.filter((candidate) => candidate.id !== game.id))
      setCompareNotice('')
      return
    }

    if (compareList.length >= 3) {
      setCompareNotice('比較できるゲームは3件までです。1件外してから追加してください。')
      return
    }

    setCompareList((current) => [...current, game])
    setCompareNotice('')
  }

  if (isBattleMode) {
    return (
      <div className="game-detail-content comparison-page">
        <div className="comparison-page__header">
          <h1 className="game-title">COMPARISON BATTLE</h1>
          <button type="button" className="filter-btn" onClick={() => setIsBattleMode(false)}>CLOSE BATTLE</button>
        </div>

        <div className="battle-grid">
          {compareList.map((game) => (
            <div key={game.id} className="battle-col">
              <div className="pro-card comparison-game-card">
                <img src={gameImageUrl(game)} onError={handleGameImageError} className="comparison-game-image" alt={game.title_ja || game.title || ''} />
                <div className="pro-stat-value">{game.title_ja || game.title}</div>
                {game.strategy_tier && <div className="tier-badge comparison-tier">TIER {game.strategy_tier}</div>}
              </div>

              <div className="battle-attr">
                <div className="battle-attr-label">Synopsis</div>
                <div className="comparison-summary">{game.summary || 'No summary available.'}</div>
              </div>

              <div className="battle-attr">
                <div className="battle-attr-label">Specs</div>
                <div className="pro-stats-grid comparison-specs">
                  <div className="pro-stat-card"><div className="pro-stat-label">P</div><div className="pro-stat-value comparison-stat">{game.min_players}-{game.max_players}</div></div>
                  <div className="pro-stat-card"><div className="pro-stat-label">T</div><div className="pro-stat-value comparison-stat">{game.play_time}m</div></div>
                </div>
              </div>

              {game.structured_data?.mechanics && (
                <div className="battle-attr">
                  <div className="battle-attr-label">Mechanics</div>
                  <div className="tag-list">
                    {game.structured_data.mechanics.slice(0, 5).map((mechanic) => <span key={mechanic} className="tag-item">{mechanic}</span>)}
                  </div>
                </div>
              )}

              <Link to={`/games/${game.slug}`} className="filter-btn comparison-detail-link">VIEW FULL ANALYSIS</Link>
            </div>
          ))}
        </div>
      </div>
    )
  }

  const filterProps = {
    activePlayers,
    activeTime,
    activeTier,
    availableTiers,
    setActivePlayers,
    setActiveTime,
    setActiveTier,
    clearFilters,
  }

  return (
    <>
      <header>
        <Link to="/" className="logo">
          <div className="logo-text">ボドゲのミカタ</div>
        </Link>

        <form className="search-container directory-search" role="search" onSubmit={handleDirectorySearch}>
          <label htmlFor="game-directory-search" className="sr-only">ゲームを検索</label>
          <input
            id="game-directory-search"
            type="search"
            className="search-input"
            placeholder="ゲーム名・概要で検索"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
          />
          <button
            type="button"
            className="filter-btn generate-game-button"
            disabled={!query.trim() || generating}
            onClick={handleGenerateGame}
          >
            {generating ? '生成中…' : '未登録ゲームをAIで追加'}
          </button>
        </form>

        <div className="db-status" aria-label={loading ? 'ゲーム一覧を同期中' : `${totalGamesCount}件のゲーム`}>
          <div className="status-dot connected"></div>
          {loading ? 'SYNCING...' : `${totalGamesCount} GAMES`}
        </div>
      </header>

      {mobileFiltersOpen && (
        <button
          type="button"
          className="mobile-filter-backdrop"
          aria-label="フィルターを閉じる"
          onClick={() => setMobileFiltersOpen(false)}
        />
      )}

      <aside id="directory-filters" className={`filter-sidebar-shell ${mobileFiltersOpen ? 'mobile-open' : ''}`} aria-label="ゲーム絞り込み">
        <button type="button" className="filter-btn mobile-filter-close" onClick={() => setMobileFiltersOpen(false)}>
          フィルターを閉じる
        </button>
        <Filters {...filterProps} />
      </aside>

      <main>
        <div className="control-panel">
          <div className="active-filters">
            <button
              type="button"
              className="filter-btn mobile-filter-toggle"
              aria-expanded={mobileFiltersOpen}
              aria-controls="directory-filters"
              onClick={() => setMobileFiltersOpen(true)}
            >
              フィルター
            </button>
            <span className="results-count">{filteredGames.length} RESULTS</span>
            {activePlayers && <div className="filter-chip">人数: {activePlayers} <button type="button" aria-label="人数フィルターを解除" onClick={() => setActivePlayers(null)}>×</button></div>}
            {activeTime && <div className="filter-chip">時間: {activeTime} <button type="button" aria-label="時間フィルターを解除" onClick={() => setActiveTime(null)}>×</button></div>}
            {activeTier && <div className="filter-chip">Tier: {activeTier} <button type="button" aria-label="戦略Tierフィルターを解除" onClick={() => setActiveTier(null)}>×</button></div>}
          </div>

          <label htmlFor="game-sort" className="sr-only">ゲームの並び順</label>
          <select id="game-sort" className="sort-select" value={sortOption} onChange={(event) => setSortOption(event.target.value)}>
            <option value="recent">最近追加</option>
            <option value="title">タイトル順</option>
            <option value="year">発売年順</option>
            <option value="play_time">プレイ時間順</option>
          </select>
        </div>

        {error && <div className="app-feedback app-feedback--error" role="alert">{error}</div>}
        {generating && <div className="app-feedback app-feedback--progress" role="status">未登録ゲームの情報を生成しています…</div>}
        {compareNotice && <div className="app-feedback compare-feedback" role="status">{compareNotice}</div>}

        {loading ? (
          <div className="app-loading-state" role="status">ARCHIVE INITIALIZING...</div>
        ) : (
          <div className="asset-grid">
            {filteredGames.map((game) => {
              const selected = compareList.some((candidate) => candidate.id === game.id)
              const limitReached = compareList.length >= 3 && !selected
              const title = game.title_ja || game.title || 'このゲーム'
              return (
                <div key={game.id} className="asset-card-shell">
                  <Link to={`/games/${game.slug}`} className="asset-card asset-card-link">
                    <div className="asset-thumb-container">
                      {game.strategy_tier && <div className="tier-badge">Tier {game.strategy_tier}</div>}
                      <img src={gameImageUrl(game)} onError={handleGameImageError} alt={title} className="asset-thumb" loading="lazy" />
                    </div>
                    <div className="asset-info">
                      <div className="asset-title">{title}</div>
                      <div className="asset-meta">
                        {game.min_players && <span className="meta-item">👥 {game.min_players}{game.max_players && game.max_players !== game.min_players ? `-${game.max_players}` : ''}</span>}
                        {game.play_time && <span className="meta-item">⏳ {game.play_time}m</span>}
                        {game.published_year && <span className="meta-item">📅 {game.published_year}</span>}
                      </div>
                      <div className="asset-summary">{game.summary || game.description}</div>
                    </div>
                  </Link>
                  <button
                    type="button"
                    className={`filter-btn compare-toggle ${selected ? 'active' : ''}`}
                    aria-pressed={selected}
                    aria-label={selected ? `${title}を比較から外す` : `${title}を比較に追加`}
                    disabled={limitReached}
                    title={limitReached ? '比較は3件までです' : undefined}
                    onClick={() => toggleCompare(game)}
                  >
                    {selected ? 'READY' : limitReached ? 'MAX 3' : 'COMPARE'}
                  </button>
                </div>
              )
            })}
            {filteredGames.length === 0 && !loading && <div className="app-empty-state">条件に一致するゲームが見つかりません。</div>}
          </div>
        )}

        {!loading && initialGames.length < totalGamesCount && (
          <div className="load-more-wrap">
            <button type="button" className="filter-btn load-more-button" onClick={handleLoadMore}>
              さらに読み込む ({initialGames.length} / {totalGamesCount})
            </button>
          </div>
        )}
      </main>

      {compareList.length > 0 && (
        <div className="comparison-tray" role="region" aria-label={`比較トレイ ${compareList.length}/3`}>
          <div className="comparison-tray__label">BATTLE TRAY · {compareList.length}/3</div>
          {compareList.map((game) => {
            const title = game.title_ja || game.title || 'ゲーム'
            return (
              <div key={game.id} className="compare-item">
                <img src={gameImageUrl(game)} onError={handleGameImageError} alt={title} />
                <button type="button" aria-label={`${title}を比較から外す`} onClick={() => toggleCompare(game)}>×</button>
              </div>
            )
          })}
          {compareList.length >= 2 && (
            <button type="button" className="filter-btn active battle-start-button" onClick={() => setIsBattleMode(true)}>
              BATTLE START
            </button>
          )}
        </div>
      )}
    </>
  )
}

export default App