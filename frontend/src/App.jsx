import { useEffect, useState } from 'react'
import GamePage from './pages/GamePage'

// Simple API client
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
  }
}

function App() {
  // State
  const [games, setGames] = useState([])
  const [initialGames, setInitialGames] = useState([])
  const [selectedSlug, setSelectedSlug] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [query, setQuery] = useState('')

  // Initial Load
  useEffect(() => {
    const load = async () => {
      try {
        setLoading(true)
        const data = await api.get('/api/games')
        const list = Array.isArray(data) ? data : data.games || []

        // Normalize data
        const normalized = list.map(g => ({
          ...g,
          slug: g.slug || g.game_slug || String(g.id),
          name: g.name || g.title || 'Untitled'
        }))

        setGames(normalized)
        setInitialGames(normalized)

        // Auto-select first game
        if (normalized.length > 0) {
          setSelectedSlug(normalized[0].slug)
        }
      } catch (e) {
        console.error('Load failed:', e)
        setError('ゲームの読み込みに失敗しました。')
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  // Search Handler
  const handleSearch = async (e) => {
    e.preventDefault()
    if (!query.trim()) {
      setGames(initialGames)
      return
    }

    try {
      setLoading(true)
      const data = await api.post('/api/search', { query })
      const list = Array.isArray(data) ? data : data.games || []

      const normalized = list.map(g => ({
        ...g,
        slug: g.slug || g.game_slug || String(g.id),
        name: g.name || g.title || 'Untitled'
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
    }
  }

  const handleClear = () => {
    setQuery('')
    setGames(initialGames)
    if (initialGames.length > 0) {
      setSelectedSlug(initialGames[0].slug)
    }
  }

  return (
    <div className="app-container">
      {/* Header */}
      <header className="main-header">
        <div className="brand" onClick={handleClear}>
          <span className="logo-icon">♜</span>
          <h1>ボドゲのミカタ</h1>
        </div>
        <nav>
          <a href="/data" className="nav-link">📊 データ</a>
        </nav>
      </header>

      {/* Search Bar */}
      <div className="search-section">
        <form onSubmit={handleSearch} className="search-form">
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="ゲーム名で検索..."
            className="search-input"
          />
          <button type="submit" className="btn-primary" disabled={loading}>
            {loading ? '...' : '検索'}
          </button>
          {query && (
            <button type="button" onClick={handleClear} className="btn-ghost">
              クリア
            </button>
          )}
        </form>
      </div>

      {/* Error Message */}
      {error && <div className="error-banner">{error}</div>}

      {/* Main Layout */}
      <main className="main-layout">
        {/* Left Pane: Game List */}
        <aside className="game-list-pane">
          <div className="pane-header">
            <h2>ゲーム一覧 <span className="count">{games.length}</span></h2>
          </div>

          <div className="game-grid">
            {games.map(game => (
              <div
                key={game.slug}
                className={`game-card ${selectedSlug === game.slug ? 'active' : ''}`}
                onClick={() => setSelectedSlug(game.slug)}
              >
                <h3 className="game-title">{game.name}</h3>
                <p className="game-summary">
                  {game.structured_data?.summary || game.description || 'No description'}
                </p>
                {game.structured_data?.keywords && (
                  <div className="game-tags">
                    {game.structured_data.keywords.slice(0, 2).map((k, i) => (
                      <span key={i} className="tag">{k.term}</span>
                    ))}
                  </div>
                )}
              </div>
            ))}

            {games.length === 0 && !loading && (
              <div className="empty-state">
                ゲームが見つかりませんでした。
              </div>
            )}
          </div>
        </aside>

        {/* Right Pane: Game Detail */}
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

      <footer className="main-footer">
        © {new Date().getFullYear()} ボドゲのミカタ
      </footer>
    </div>
  )
}

export default App
