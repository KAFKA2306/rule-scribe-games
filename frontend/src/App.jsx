import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import GamePage from './pages/GamePage'
import { ThinkingMeeple } from './components/ThinkingMeeple'
import { EmptyMeeple } from './components/EmptyMeeple'
import { GameBackground } from './components/GameBackground'
import { supabase } from './lib/supabase'

import { api } from './lib/api'

function App() {
  const [searchParams, setSearchParams] = useSearchParams()
  const [games, setGames] = useState([])
  const [initialGames, setInitialGames] = useState([])
  const [selectedSlug, setSelectedSlug] = useState(null)
  const [loading, setLoading] = useState(true)
  const [loadingMore, setLoadingMore] = useState(false)
  const [generating, setGenerating] = useState(false)
  const [error, setError] = useState(null)
  const [_session, setSession] = useState(null)

  useEffect(() => {
    if (!supabase) return
    supabase.auth.getSession().then(({ data: { session } }) => {
      setSession(session)
    })

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, session) => {
      setSession(session)
    })

    return () => subscription.unsubscribe()
  }, [])

  const [query, setQuery] = useState(searchParams.get('q') || '')
  const [hasMore, setHasMore] = useState(true)
  const [offset, setOffset] = useState(0)

  const loadGames = async (currentOffset = 0, append = false) => {
      setError(null)
      if (!append) setLoading(true)
      else setLoadingMore(true)

      const data = await api.get(`/api/games?limit=50&offset=${currentOffset}`)
      const list = Array.isArray(data) ? data : data.games || []

      if (append) {
        setGames((prev) => [...prev, ...list])
        setInitialGames((prev) => [...prev, ...list])
      } else {
        setGames(list)
        setInitialGames(list)
        if (list.length > 0) {
          setSelectedSlug(list[0].slug)
        }
      }

      setHasMore(list.length === 50)
      setOffset(currentOffset + list.length)

      setLoading(false)
      setLoadingMore(false)
  }

  useEffect(() => {
    loadGames(0, false)
  }, [])

  const [debouncedQuery, setDebouncedQuery] = useState(query)

  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedQuery(query)
    }, 300)
    return () => clearTimeout(timer)
  }, [query])

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

        const data = await api.post('/api/search', { query: debouncedQuery, generate: false })
        const list = Array.isArray(data) ? data : data.games || []
        setGames(list)
    }

    searchRealtime()
  }, [debouncedQuery, initialGames])

  const handleSearch = async (e) => {
    e.preventDefault()
    if (!query.trim()) {
      setGames(initialGames)
      return
    }

      setLoading(true)
      setGenerating(true)
      setError(null)

      const data = await api.post('/api/search', { query, generate: true })
      const list = Array.isArray(data) ? data : data.games || []

      setGames(list)
      if (list.length > 0) {
        setSelectedSlug(list[0].slug)
      }

      setLoading(false)
      setGenerating(false)
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
      <GameBackground games={initialGames} />
      <header className="main-header">
        <div className="brand" onClick={handleClear}>
          <img
            src="/assets/header-icon.png"
            alt="Meeple"
            style={{ width: '32px', height: 'auto', marginRight: '8px' }}
          />
          <span className="logo-icon">♜</span>
          <h1>ボドゲのミカタ</h1>
        </div>
        <nav style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
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
            placeholder="ボードゲーム名を入れてね。なければ調べるよ！"
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
        <div
          style={{
            marginBottom: '24px',
            background: 'var(--card-bg)',
            border: '1px solid var(--primary)',
            borderRadius: '12px',
            padding: '16px',
          }}
        >
          <ThinkingMeeple text="AIがルールブックを読破中... (30〜60秒ほどお待ちください)" />
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
            {loading && (
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'center',
                  padding: '48px',
                  width: '100%',
                }}
              >
                <ThinkingMeeple />
              </div>
            )}
            {games.map((game) => {
              const title = game.title_ja || game.title || game.name || 'Untitled'
              return (
                <div
                  key={game.slug}
                  className={`game-card ${selectedSlug === game.slug ? 'active' : ''}`}
                  onClick={() => setSelectedSlug(game.slug)}
                  style={{
                    backgroundImage: `linear-gradient(rgba(0,0,0,0.7), rgba(0,0,0,0.8)), url(/assets/games/${game.slug}.png)${
                      game.image_url ? `, url(${game.image_url})` : ''
                    }`,
                    backgroundSize: 'cover',
                    backgroundPosition: 'center',
                  }}
                >
                  <h3 className="game-title">{title}</h3>
                  <p className="game-summary">{game.summary || game.description}</p>
                  <div className="game-tags">
                    <span className="tag">
                      {game.min_players}-{game.max_players}人用
                    </span>
                    <span className="tag">{game.play_time}分</span>
                  </div>
                </div>
              )
            })}

            {games.length === 0 && !loading && <EmptyMeeple query={query} />}

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
              <div style={{ textAlign: 'center', padding: '20px' }}>📚 さらに読み込み中...</div>
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

export default App
