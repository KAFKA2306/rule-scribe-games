import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import GamePage from './pages/GamePage'

const post = async (path, payload, setLoading) => {
  setLoading(true)
  const res = await fetch(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!res.ok) throw new Error(await res.text())
  const data = await res.json()
  setLoading(false)
  return data
}

function App() { // Renamed from Home to App
  const [query, setQuery] = useState('')
  const [initialGames, setInitialGames] = useState([])
  const [games, setGames] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const clear = () => {
    setQuery('')
    setError('')
    if (initialGames.length > 0) {
      setGames(initialGames)
    } else {
      setGames([])
    }
  }

  useEffect(() => {
    const loadInitial = async () => {
      setLoading(true)
      try {
        const res = await fetch('/api/games')
        if (!res.ok) throw new Error(await res.text())
        const data = await res.json()
        setInitialGames(data)
        setGames(data)
      } catch (e) {
        console.error('Failed to load initial games:', e)
      } finally {
        setLoading(false)
      }
    }
    loadInitial()
  }, [])

  const search = async (e) => {
    e.preventDefault()
    const q = query.trim()
    if (!q) return
    setError('')
    setGames([])

    try {
      const data = await post('/api/search', { query: q }, setLoading)
      if (data.error) {
        setError(data.error)
      } else {
        setGames(data)
      }
    } catch (e) {
      setError(e.message)
    }
  }

  return (
    <div className="app">
      <header>
        <div className="brand" onClick={clear}>
          ボドゲのミカタ
        </div>
        <span className="muted">ルール、わからなくなっても大丈夫。</span>
        <Link to="/data" className="data-link">
          📊 データ
        </Link>
      </header>

      <form onSubmit={search}>
        <input
          placeholder="ゲームの名前を入れてね"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <button type="submit" disabled={loading}>
          {loading ? '考え中...' : 'さがす'}
        </button>
        <button type="button" className="secondary" onClick={clear}>
          クリア
        </button>
      </form>

      {error && (
        <p className="error">
          {error.includes('API Error')
            ? 'AIサービスの呼び出しに失敗しました。しばらく待ってからもう一度お試しください。'
            : error}
        </p>
      )}

      <div className="layout">
        <section className="results panel" style={{ width: '100%' }}>
          <div className="section-head">
            <h2>見つかったゲーム</h2>
            {games.length > 0 && (
              <span className="pill">
                <span style={{ fontWeight: 700 }}>{games.length}</span> titles
              </span>
            )}
          </div>
          {games.length === 0 ? (
            <p className="muted">まずは検索してみてね。</p>
          ) : (
            <ul>
              {games.map((game) => (
                <li key={game.id ?? game.title}>
                  <Link
                    to={`/games/${game.slug}`}
                    style={{ textDecoration: 'none', color: 'inherit', display: 'block' }}
                  >
                    <strong>{game.title}</strong>
                    <small>{game.description || '説明がないみたい。'}</small>
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </section>
      </div>

      <footer className="muted">© {new Date().getFullYear()} ボドゲのミカタ</footer>
    </div>
  )
}

export default App

