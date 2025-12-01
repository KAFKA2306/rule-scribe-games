import { useState } from 'react'
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
  const [games, setGames] = useState([])
  const [pick, setPick] = useState(null)
  const [summary, setSummary] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const clear = () => {
    setQuery('')
    setGames([])
    setPick(null)
    setSummary('')
    setError('')
  }

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
        <section className="results">
          <div className="section-head">
            <h2>見つかったゲーム</h2>
            {games.length > 0 && <span className="muted">{games.length}</span>}
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

        <section className="detail">
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
