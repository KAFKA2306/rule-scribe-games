import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import GamePage from './pages/GamePage'

const api = {
  get: async (path) => {
    const res = await fetch(path)
    if (!res.ok) throw new Error(`API Error: ${res.status}`)
    return res.json()
  },
  post: async (path, body) => {
    const res = await fetch(path, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })
    if (!res.ok) throw new Error(`API Error: ${res.status}`)
    return res.json()
  },
}

function App() {
  const [searchParams, setSearchParams] = useSearchParams()
  const [games, setGames] = useState([])
  const [initialGames, setInitialGames] = useState([])
  const [selectedSlug, setSelectedSlug] = useState(null)
  const [loading, setLoading] = useState(true)
  const [loadingMore, setLoadingMore] = useState(false)
  const [generating, setGenerating] = useState(false)
  const [error, setError] = useState(null)

  // Initialize query from URL
  const [query, setQuery] = useState(searchParams.get('q') || '')
  const [hasMore, setHasMore] = useState(true)
  const [offset, setOffset] = useState(0)

  // ... loadGames ...

  const [debouncedQuery, setDebouncedQuery] = useState(query)

  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedQuery(query)
    }, 300)
    return () => clearTimeout(timer)
  }, [query])

  // Sync URL with debounced query
  useEffect(() => {
    if (debouncedQuery) {
      setSearchParams({ q: debouncedQuery }, { replace: true })
    } else {
      setSearchParams({}, { replace: true })
    }
  }, [debouncedQuery, setSearchParams])

  useEffect(() => {
    const searchRealtime = async () => {
      if (!debouncedQuery.trim()) {
        setGames(initialGames)
        return
      }

      try {
        const data = await api.post('/api/search', { query: debouncedQuery, generate: false })
        const list = Array.isArray(data) ? data : data.games || []

        const normalized = list.map((g) => ({
          ...g,
          slug: g.slug || g.game_slug || String(g.id),
          name: g.name || g.title || 'Untitled',
        }))

        setGames(normalized)
      } catch (e) {
        console.error('Real-time search failed:', e)
      }
    }

    searchRealtime()
  }, [debouncedQuery, initialGames])

  const handleSearch = async (e) => {
    e.preventDefault()
    if (!query.trim()) {
      setGames(initialGames)
      return
    }

    try {
      setLoading(true)
      setGenerating(true)

      const data = await api.post('/api/search', { query, generate: true })
      const list = Array.isArray(data) ? data : data.games || []

      const normalized = list.map((g) => ({
        ...g,
        slug: g.slug || g.game_slug || String(g.id),
        name: g.name || g.title || 'Untitled',
      }))

      setGames(normalized)
      if (normalized.length > 0) {
        setSelectedSlug(normalized[0].slug)
      }
    } catch (e) {
      console.error('Search failed:', e)
      setError('検索に失敗しました。')
    } finally {
      setLoading(false)
      setGenerating(false)
    }
  }

  const handleClear = () => {
    setQuery('')
    setDebouncedQuery('')
    setGames(initialGames)
    if (initialGames.length > 0) {
      setSelectedSlug(initialGames[0].slug)
    }
  }

  return (
    <div className="app-container">
      <header className="main-header">
        <div className="brand" onClick={handleClear}>
          <span className="logo-icon">♜</span>
          <h1>ボドゲのミカタ</h1>
        </div>
        <nav>
          <a href="/data" className="nav-link">
            📊 データ
          </a>
        </nav>
      </header>

      <div className="search-section">
        <form onSubmit={handleSearch} className="search-form">
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="ゲーム名で検索..."
            className="search-input"
          />
          <button type="submit" className="btn-primary" disabled={loading}>
            {loading ? '検索中...' : '検索'}
          </button>
          {query && (
            <button type="button" onClick={handleClear} className="btn-ghost">
              クリア
            </button>
          )}
        </form>
      </div>

      {error && <div className="error-banner">{error}</div>}
      {generating && (
        <div className="generating-banner">
          <div className="spinner"></div>
          <span>🎲 新しいボードゲームを調査中... (30-60秒かかります)</span>
        </div>
      )}

      <main className="main-layout">
        <aside className="game-list-pane">
          <div className="pane-header">
            <h2>
              ゲーム一覧 <span className="count">{games.length}</span>
            </h2>
          </div>

          <div className="game-grid">
            {games.map((game) => (
              <div
                key={game.slug}
                className={`game-card ${selectedSlug === game.slug ? 'active' : ''}`}
                onClick={() => setSelectedSlug(game.slug)}
                style={{
                  backgroundImage: game.image_url
                    ? `linear-gradient(rgba(0,0,0,0.7), rgba(0,0,0,0.8)), url(${game.image_url})`
                    : 'none',
                  backgroundSize: 'cover',
                  backgroundPosition: 'center',
                }}
              >
                <h3 className="game-title">{game.name}</h3>
                <p className="game-summary">{game.description}</p>
                <div className="game-tags">
                  <span className="tag">
                    {game.min_players}-{game.max_players}人用
                  </span>
                  <span className="tag">{game.play_time}分</span>
                </div>
              </div>
            ))}

            {games.length === 0 && !loading && (
              <div className="empty-state">ゲームが見つかりませんでした。</div>
            )}

            {hasMore && !query && !loading && (
              <div
                ref={(node) => {
                  if (node && !loadingMore && !loading) {
                    const observer = new IntersectionObserver(
                      (entries) => {
                        if (entries[0].isIntersecting) {
                          loadGames(offset, true)
                        }
                      },
                      { threshold: 0.1 }
                    )
                    observer.observe(node)
                    return () => observer.disconnect()
                  }
                }}
                style={{ height: '20px', margin: '10px 0' }}
              />
            )}

            {loadingMore && (
              <div style={{ textAlign: 'center', padding: '20px' }}>読み込み中...</div>
            )}
          </div>
        </aside>

        <section className="game-detail-pane">
          {selectedSlug ? (
            <GamePage slug={selectedSlug} />
          ) : (
            <div className="empty-selection">
              <p>左のリストからゲームを選択してください</p>
            </div>
          )}
        </section>
      </main>

      <footer className="main-footer">© {new Date().getFullYear()} ボドゲのミカタ</footer>
    </div>
  )
}

export default App
