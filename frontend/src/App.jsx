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
  // HasMore/Offset are no longer needed for full client-side load
  // const [hasMore, setHasMore] = useState(true)
  // const [offset, setOffset] = useState(0)

  useEffect(() => {
    const loadAllGames = async () => {
      setError(null)
      setLoading(true)

      try {
        // Fetch a large number to ensure we get everything for client-side search
        const data = await api.get(`/api/games?limit=1000&offset=0`)
        const list = Array.isArray(data) ? data : data.games || []

        setInitialGames(list)
        // If there's an initial query from URL, filtered results will be set by the useEffect below
        // Otherwise, show all
        if (!searchParams.get('q')) {
          setGames(list)
          if (list.length > 0) {
            setSelectedSlug(list[0].slug)
          }
        } else {
          // Initial filter will happen in useEffect
        }

      } catch (err) {
        console.error('Failed to load games:', err)
        setError('ゲームの読み込みに失敗しました。しばらく経ってから再読み込みしてください。')
      } finally {
        setLoading(false)
      }
    }

    loadAllGames()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const [debouncedQuery, setDebouncedQuery] = useState(query)

  // Debounce input
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedQuery(query)
    }, 300)
    return () => clearTimeout(timer)
  }, [query])

  // Sync with URL
  useEffect(() => {
    if (debouncedQuery) {
      setSearchParams({ q: debouncedQuery }, { replace: true })
    } else {
      setSearchParams({}, { replace: true })
    }
  }, [debouncedQuery, setSearchParams])

  // Client-side wide search
  useEffect(() => {
    if (initialGames.length === 0) return

    const q = debouncedQuery.trim().toLowerCase()

    if (!q) {
      setGames(initialGames)
      return
    }

    console.log('Filtering games with query:', q)
    console.log('Sample game:', initialGames[0])

    const filtered = initialGames.filter((game) => {
      const title = (game.title || '').toLowerCase()
      const titleJa = (game.title_ja || '').toLowerCase()
      const titleEn = (game.title_en || '').toLowerCase()
      const summary = (game.summary || '').toLowerCase()
      const description = (game.description || '').toLowerCase()
      const rules = (game.rules_content || '').toLowerCase()

      if (game.slug === 'splendor') {
        console.log('Checking Splendor:', {
          title, titleJa, titleEn, summary, description, rules,
          q,
          match: title.includes(q) || titleJa.includes(q) || titleEn.includes(q)
        })
      }

      return (
        title.includes(q) ||
        titleJa.includes(q) ||
        titleEn.includes(q) ||
        summary.includes(q) ||
        description.includes(q) ||
        rules.includes(q)
      )
    })

    setGames(filtered)
    // Optional: Select first result if current selection is not in list?
    // For now, let's keep selection logic simple.
  }, [debouncedQuery, initialGames])


  const handleSearch = async (e) => {
    e.preventDefault()
    // For normal search, the useEffect handles it.
    // This handler is now primarily for "Generate" (Force create new).

    // If just searching existing, do nothing (handled by effect)
    // But if we want to support "Generate" explicitly via button:
    // We already filter. If user hits Enter, it's just submitting the form.

    // However, the original code had "Generate" button logic associated with `generating` state.
    // The UI shows a "Generate" button.

    if (!query.trim()) {
      return
    }

    // Check if we have results locally. If we do, usually we don't auto-generate.
    // But the button says "Generate".
    // Let's assume the button action is specifically to TRY generating if not found, 
    // or if the user explicitly wants to find something new.

    // Changing behavior: "Search" happens automatically. 
    // "Generate" button should specifically trigger the API generation.

    setLoading(true)
    setGenerating(true)
    setError(null)

    try {
      // Use the generate=true flag
      const data = await api.post('/api/search', { query, generate: true })
      const list = Array.isArray(data) ? data : data.games || []

      // If a new game was generated, it usually returns just that game or a list.
      // We should probably re-fetch all games or add this to our local list.
      if (list.length > 0) {
        const newGame = list[0]
        // Check if we already have it
        const exists = initialGames.find(g => g.slug === newGame.slug)
        if (!exists) {
          const newTotal = [newGame, ...initialGames]
          setInitialGames(newTotal)
          // The useEffect will re-filter and pick it up
        }
        setQuery(newGame.title_ja || newGame.title) // update query to match exact title? Maybe not.
        setSelectedSlug(newGame.slug)
      }
    } catch (e) {
      console.error(e)
      setError("生成に失敗しました。")
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
      <GameBackground games={initialGames} />
      <header className="main-header">
        <div className="brand" onClick={handleClear}>
          <img
            src="/assets/header-icon.webp"
            alt="Meeple"
            loading="lazy"
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

      <div style={{ textAlign: 'center', margin: '24px 16px', color: '#a0aec0', fontSize: '0.95rem', lineHeight: '1.6' }}>
        <p style={{ margin: 0 }}>
          「説明書を読むのが面倒」「インスト準備に時間がかかる」そんな悩みをAIが解決。<br />
          ボドゲのミカタは、世界中のボードゲームのルールを瞬時に要約・検索できるツールです。
        </p>
      </div>

      <div className="search-section">
        <form onSubmit={handleSearch} className="search-form">
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="ボードゲーム名を入れてね。なければ調べるよ！"
            className="search-input"
          />
          <button type="submit" className="btn-primary" disabled={loading || generating}>
            {generating ? '生成中...' : '生成'}
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
          <ThinkingMeeple text="探検家ミープル君がルールブックを読破中..." />
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
                    backgroundImage: `linear-gradient(rgba(0,0,0,0.7), rgba(0,0,0,0.8)), url(/assets/games/${game.slug}.webp)${game.image_url ? `, url(${game.image_url})` : ''
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


          </div>
        </aside>

        <section className="game-detail-pane">
          {selectedSlug ? (
            <GamePage key={selectedSlug} slug={selectedSlug} initialGame={games.find(g => g.slug === selectedSlug)} />
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
