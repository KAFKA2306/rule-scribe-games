import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import ReactMarkdown from 'react-markdown'

const post = async (path, payload, onError, setLoading) => {
  setLoading(true)
  try {
    const res = await fetch(path, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })
    if (!res.ok) throw new Error(await res.text())
    return await res.json()
  } catch (err) {
    console.error(err)
    onError('ごめんね、うまくいかなかったみたい。')
    return null
  } finally {
    setLoading(false)
  }
}

function App() {
  const [query, setQuery] = useState('')
  const [initialGames, setInitialGames] = useState([])
  const [games, setGames] = useState([])
  const [pick, setPick] = useState(null)
  const [summary, setSummary] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const clear = () => {
    setQuery('')
    setError('')
    setSummary('')
    if (initialGames.length > 0) {
      setGames(initialGames)
      const first = initialGames[0] || null
      setPick(first)
      if (first?.summary) setSummary(first.summary)
    } else {
      setGames([])
      setPick(null)
    }
  }

  useEffect(() => {
    let canceled = false
    const loadInitial = async () => {
      setLoading(true)
      try {
        const res = await fetch('/api/games')
        if (!res.ok) throw new Error(await res.text())
        const data = await res.json()
        if (canceled) return
        setInitialGames(data)
        setGames(data)
        const first = data[0] || null
        setPick(first)
        if (first?.summary) setSummary(first.summary)
      } catch (err) {
        console.error(err)
        if (!canceled) {
          setError('Supabaseから初期データを読み込めませんでした。検索してみてね。')
        }
      } finally {
        if (!canceled) setLoading(false)
      }
    }
    loadInitial()
    return () => {
      canceled = true
    }
  }, [])

  const search = async (e) => {
    e.preventDefault()
    const q = query.trim()
    if (!q) return
    setError('')
    setSummary('')
    setPick(null)
    setGames([])
    const data = await post('/api/search', { query: q }, setError, setLoading)
    if (data) {
      setGames(data)
      const first = data[0] || null
      setPick(first)
      if (first?.summary) {
        setSummary(first.summary)
      }
    }
  }

  const summarize = async () => {
    if (!pick) return
    setError('')
    const data = await post(
      '/api/summarize',
      { text: pick.rules_content || '', game_id: pick.id },
      setError,
      setLoading,
    )
    if (data) setSummary(data.summary)
  }

  return (
    <div className="app">
      <header>
        <div className="brand" onClick={clear}>ボドゲのミカタ</div>
        <span className="muted">ルール、わからなくなっても大丈夫。</span>
        <Link to="/data" className="data-link">📊 データ</Link>
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

      {error && <p className="error">{error}</p>}

      <div className="layout">
        <section className="results panel">
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
                <li
                  key={game.id ?? game.title}
                  className={pick?.id === game.id ? 'active' : ''}
                  onClick={() => {
                    setPick(game)
                    setSummary(game.summary || '')
                  }}
                >
                  <strong>{game.title}</strong>
                  <small>{game.description || '説明がないみたい。'}</small>
                </li>
              ))}
            </ul>
          )}
        </section>

        <section className="detail panel">
          {!pick ? (
            <p className="muted">リストから選ぶと、ここにルールが出るよ。</p>
          ) : (
            <>
              <div className="detail-head">
                <div>
                  <h2>{pick.title}</h2>
                  {pick.source_url && (
                    <a href={pick.source_url} target="_blank" rel="noreferrer" className="muted">
                      情報元
                    </a>
                  )}
                </div>
                <button
                  type="button"
                  onClick={summarize}
                  disabled={loading || !!summary}
                  className="secondary"
                >
                  {summary ? '要約完了！' : '要約する'}
                </button>
              </div>

              {summary && (
                <div className="summary">
                  <h3>AIのまとめ</h3>
                  <ReactMarkdown className="markdown">{summary}</ReactMarkdown>
                </div>
              )}

              {pick.structured_data?.keywords && (
                <div className="summary">
                  <h3>キーワード</h3>
                  {pick.structured_data.keywords.map((kw) => (
                    <div key={kw.term} style={{ marginBottom: '8px' }}>
                      <strong>{kw.term}</strong>: {kw.description}
                    </div>
                  ))}
                </div>
              )}

              {pick.structured_data?.popular_cards && (
                <div className="summary">
                  <h3>人気のカード/コンポーネント</h3>
                  {pick.structured_data.popular_cards.map((card) => (
                    <div key={card.name} style={{ marginBottom: '8px' }}>
                      <strong>{card.name}</strong> ({card.type}, コスト{card.cost})
                      {card.reason && <small> - {card.reason}</small>}
                    </div>
                  ))}
                </div>
              )}

              <div className="summary">
                <h3>詳しいルール</h3>
                <ReactMarkdown className="markdown">
                  {pick.rules_content || 'ルールが見つかりませんでした。'}
                </ReactMarkdown>
              </div>
            </>
          )}
        </section>
      </div>

      <footer className="muted">© {new Date().getFullYear()} ボドゲのミカタ</footer>
    </div>
  )
}

export default App
