import { useEffect, useMemo, useRef, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { api } from './lib/api'

const PLAYER_FILTERS = ['1', '2', '3', '4', '5+']
const TIME_FILTERS = [
  { id: '30-', label: '30分以内' },
  { id: '30-60', label: '30-60分' },
  { id: '60-120', label: '60-120分' },
  { id: '120+', label: '120分以上' },
]
const SORT_OPTIONS = ['recent', 'title', 'year', 'play_time']
const PAGE_SIZE = 48
const NO_IMAGE_URL = '/assets/no-image.webp'

function gameImageUrl(game) {
  const configured = game.image_url?.trim()
  if (configured && !configured.includes('placeholder') && !configured.endsWith(NO_IMAGE_URL)) return configured
  return game.slug ? `/images/games/generated/${game.slug}.webp` : NO_IMAGE_URL
}

function handleGameImageError(event) {
  if (!event.currentTarget.src.endsWith(NO_IMAGE_URL)) event.currentTarget.src = NO_IMAGE_URL
}

function comparisonPlayers(game) {
  if (!Number.isFinite(game.min_players) || game.min_players <= 0) return '不明'
  if (!Number.isFinite(game.max_players) || game.max_players <= 0) return `${game.min_players}人以上`
  return game.min_players === game.max_players ? `${game.min_players}人` : `${game.min_players}-${game.max_players}人`
}

function comparisonPlayTime(game) {
  return Number.isFinite(game.play_time) && game.play_time > 0 ? `${game.play_time}分` : '不明'
}

function directoryTrustLabel(game) {
  if (game.identity_status !== 'verified') return '未検証'
  if (!['human_reviewed', 'publisher_reviewed'].includes(game.content_review_status)) return '内容要確認'
  if (!game.source_trust || game.source_trust === 'unknown') return '出典未確認'
  if (game.source_trust === 'third_party') return '第三者出典'
  return null
}

function directoryParams({ query, players, time, tier, sort, offset = 0 }) {
  const params = new URLSearchParams()
  const trimmedQuery = query.trim()
  if (trimmedQuery) params.set('q', trimmedQuery)
  if (players) params.set('players', players)
  if (time) params.set('time', time)
  if (tier) params.set('tier', tier)
  if (sort !== 'recent') params.set('sort', sort)
  params.set('limit', String(PAGE_SIZE))
  params.set('offset', String(offset))
  return params
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
                戦略ティア {tier}
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
  const initialPlayers = searchParams.get('players')
  const initialTime = searchParams.get('time')
  const initialSort = searchParams.get('sort')

  const [initialGames, setInitialGames] = useState([])
  const [totalGamesCount, setTotalGamesCount] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [reloadKey, setReloadKey] = useState(0)

  const [query, setQuery] = useState((searchParams.get('q') || '').slice(0, 200))
  const [activePlayers, setActivePlayers] = useState(PLAYER_FILTERS.includes(initialPlayers) ? initialPlayers : null)
  const [activeTime, setActiveTime] = useState(TIME_FILTERS.some((time) => time.id === initialTime) ? initialTime : null)
  const [activeTier, setActiveTier] = useState((searchParams.get('tier') || '').slice(0, 40) || null)
  const [sortOption, setSortOption] = useState(SORT_OPTIONS.includes(initialSort) ? initialSort : 'recent')
  const [mobileFiltersOpen, setMobileFiltersOpen] = useState(false)

  const [compareList, setCompareList] = useState([])
  const [compareNotice, setCompareNotice] = useState('')
  const [isBattleMode, setIsBattleMode] = useState(false)
  const requestVersion = useRef(0)

  useEffect(() => {
    const nextQuery = (searchParams.get('q') || '').slice(0, 200)
    const nextPlayers = searchParams.get('players')
    const nextTime = searchParams.get('time')
    const nextTier = (searchParams.get('tier') || '').slice(0, 40) || null
    const nextSort = searchParams.get('sort')

    if (nextQuery !== query) setQuery(nextQuery)
    const validPlayers = PLAYER_FILTERS.includes(nextPlayers) ? nextPlayers : null
    if (validPlayers !== activePlayers) setActivePlayers(validPlayers)
    const validTime = TIME_FILTERS.some((time) => time.id === nextTime) ? nextTime : null
    if (validTime !== activeTime) setActiveTime(validTime)
    if (nextTier !== activeTier) setActiveTier(nextTier)
    const validSort = SORT_OPTIONS.includes(nextSort) ? nextSort : 'recent'
    if (validSort !== sortOption) setSortOption(validSort)
  }, [searchParams])

  useEffect(() => {
    const version = requestVersion.current + 1
    requestVersion.current = version
    const delay = query.trim() ? 300 : 0
    const timer = window.setTimeout(async () => {
      const urlParams = directoryParams({
        query,
        players: activePlayers,
        time: activeTime,
        tier: activeTier,
        sort: sortOption,
      })
      const browserParams = new URLSearchParams(urlParams)
      browserParams.delete('limit')
      browserParams.delete('offset')
      setSearchParams(browserParams, { replace: true })

      setError(null)
      setLoading(true)
      try {
        const data = await api.get(`/api/games?${urlParams.toString()}`)
        if (requestVersion.current !== version) return
        setInitialGames(data.games || [])
        setTotalGamesCount(data.total || 0)
      } catch (err) {
        if (requestVersion.current !== version) return
        console.error('Failed to load games:', err)
        setError('ゲームの読み込みに失敗しました。')
      } finally {
        if (requestVersion.current === version) setLoading(false)
      }
    }, delay)

    return () => window.clearTimeout(timer)
  }, [query, activePlayers, activeTime, activeTier, sortOption, reloadKey, setSearchParams])

  const handleLoadMore = async () => {
    if (initialGames.length >= totalGamesCount || loading) return
    const version = requestVersion.current + 1
    requestVersion.current = version
    setError(null)
    setLoading(true)
    try {
      const params = directoryParams({
        query,
        players: activePlayers,
        time: activeTime,
        tier: activeTier,
        sort: sortOption,
        offset: initialGames.length,
      })
      const data = await api.get(`/api/games?${params.toString()}`)
      if (requestVersion.current !== version) return
      setInitialGames((current) => [...current, ...(data.games || [])])
      setTotalGamesCount(data.total || 0)
    } catch (err) {
      if (requestVersion.current !== version) return
      console.error('Failed to load more games:', err)
      setError('追加ゲームの読み込みに失敗しました。')
    } finally {
      if (requestVersion.current === version) setLoading(false)
    }
  }

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
    if (activeTier) tiers.add(activeTier)
    return Array.from(tiers).sort()
  }, [initialGames, activeTier])

  const handleDirectorySearch = (event) => {
    event.preventDefault()
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
          <h1 className="game-title">ゲーム比較</h1>
          <button type="button" className="filter-btn" onClick={() => setIsBattleMode(false)}>比較を閉じる</button>
        </div>

        <div className="battle-grid">
          {compareList.map((game) => (
            <div key={game.id} className="battle-col">
              <div className="pro-card comparison-game-card">
                <img src={gameImageUrl(game)} onError={handleGameImageError} className="comparison-game-image" alt={game.title_ja || game.title || ''} />
                <div className="pro-stat-value">{game.title_ja || game.title}</div>
                {directoryTrustLabel(game) && <div className="meta-item">{directoryTrustLabel(game)}</div>}
                {game.strategy_tier && <div className="tier-badge comparison-tier">戦略ティア {game.strategy_tier}</div>}
              </div>

              <div className="battle-attr">
                <div className="battle-attr-label">概要</div>
                <div className="comparison-summary">{game.summary || '概要はまだありません。'}</div>
              </div>

              <div className="battle-attr">
                <div className="battle-attr-label">基本情報</div>
                <div className="pro-stats-grid comparison-specs">
                  <div className="pro-stat-card"><div className="pro-stat-label">人数</div><div className="pro-stat-value comparison-stat">{comparisonPlayers(game)}</div></div>
                  <div className="pro-stat-card"><div className="pro-stat-label">時間</div><div className="pro-stat-value comparison-stat">{comparisonPlayTime(game)}</div></div>
                </div>
              </div>

              {game.structured_data?.mechanics && (
                <div className="battle-attr">
                  <div className="battle-attr-label">メカニクス</div>
                  <div className="tag-list">
                    {game.structured_data.mechanics.slice(0, 5).map((mechanic) => <span key={mechanic} className="tag-item">{mechanic}</span>)}
                  </div>
                </div>
              )}

              <Link to={`/games/${game.slug}`} className="filter-btn comparison-detail-link">詳しい情報を見る</Link>
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
            maxLength={200}
            onChange={(event) => setQuery(event.target.value)}
          />
        </form>

        <div className="db-status" aria-label={loading ? 'ゲーム一覧を同期中' : `${totalGamesCount}件のゲーム`}>
          <div className="status-dot connected"></div>
          {loading ? '同期中…' : `${totalGamesCount}件のゲーム`}
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
            <span className="results-count">{totalGamesCount}件</span>
            {activePlayers && <div className="filter-chip">人数: {activePlayers} <button type="button" aria-label="人数フィルターを解除" onClick={() => setActivePlayers(null)}>×</button></div>}
            {activeTime && <div className="filter-chip">時間: {TIME_FILTERS.find((time) => time.id === activeTime)?.label || activeTime} <button type="button" aria-label="時間フィルターを解除" onClick={() => setActiveTime(null)}>×</button></div>}
            {activeTier && <div className="filter-chip">戦略ティア: {activeTier} <button type="button" aria-label="戦略ティアフィルターを解除" onClick={() => setActiveTier(null)}>×</button></div>}
          </div>

          <label htmlFor="game-sort" className="sr-only">ゲームの並び順</label>
          <select id="game-sort" className="sort-select" value={sortOption} onChange={(event) => setSortOption(event.target.value)}>
            <option value="recent">最近追加</option>
            <option value="title">タイトル順</option>
            <option value="year">発売年順</option>
            <option value="play_time">プレイ時間順</option>
          </select>
        </div>

        {error && (
          <div className="app-feedback app-feedback--error" role="alert">
            <span>{error}</span>
            {initialGames.length === 0 && (
              <button type="button" className="filter-btn" onClick={() => setReloadKey((value) => value + 1)}>
                再読み込み
              </button>
            )}
          </div>
        )}
        {compareNotice && <div className="app-feedback compare-feedback" role="status">{compareNotice}</div>}
        {loading && initialGames.length > 0 && <div className="app-loading-state" role="status">ゲーム一覧を更新中…</div>}

        {loading && initialGames.length === 0 ? (
          <div className="app-loading-state" role="status">ゲーム一覧を読み込み中…</div>
        ) : (
          <div className="asset-grid">
            {initialGames.map((game, index) => {
              const selected = compareList.some((candidate) => candidate.id === game.id)
              const limitReached = compareList.length >= 3 && !selected
              const title = game.title_ja || game.title || 'このゲーム'
              const trustLabel = directoryTrustLabel(game)
              return (
                <div key={game.id} className="asset-card-shell">
                  <Link to={`/games/${game.slug}`} className="asset-card asset-card-link">
                    <div className="asset-thumb-container">
                      {game.strategy_tier && <div className="tier-badge">戦略ティア {game.strategy_tier}</div>}
                      <img
                        src={gameImageUrl(game)}
                        onError={handleGameImageError}
                        alt={title}
                        className="asset-thumb"
                        loading={index === 0 ? 'eager' : 'lazy'}
                        {...{ fetchpriority: index === 0 ? 'high' : 'auto' }}
                      />
                    </div>
                    <div className="asset-info">
                      <div className="asset-title">{title}</div>
                      <div className="asset-meta">
                        {trustLabel && <span className="meta-item">{trustLabel}</span>}
                        {game.min_players && <span className="meta-item">👥 {game.min_players}{game.max_players && game.max_players !== game.min_players ? `-${game.max_players}` : ''}</span>}
                        {game.play_time && <span className="meta-item">⏳ {game.play_time}分</span>}
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
                    {selected ? '追加済み' : limitReached ? '上限3件' : '比較に追加'}
                  </button>
                </div>
              )
            })}
            {initialGames.length === 0 && !loading && !error && <div className="app-empty-state">条件に一致するゲームが見つかりません。</div>}
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
          <div className="comparison-tray__label">比較トレイ · {compareList.length}/3</div>
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
              比較する
            </button>
          )}
        </div>
      )}
    </>
  )
}

export default App
