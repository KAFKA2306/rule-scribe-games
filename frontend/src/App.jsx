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
    onError('Request failed. Check the backend or API keys.')
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
        <div className="brand" onClick={clear}>RuleScribe mini</div>
        <span className="muted">Simple search + summary for board games.</span>
      </header>

      <form onSubmit={search}>
        <input
          placeholder="Search a game name or URL"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <button type="submit" disabled={loading}>
          {loading ? 'Working...' : 'Search'}
        </button>
        <button type="button" className="secondary" onClick={clear}>
          Clear
        </button>
      </form>

      {error && <p className="error">{error}</p>}

      <div className="layout">
        <section className="results">
          <div className="section-head">
            <h2>Results</h2>
            {games.length > 0 && <span className="muted">{games.length}</span>}
          </div>
          {games.length === 0 ? (
            <p className="muted">No results yet. Try a search.</p>
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
                  <small>{game.description || 'No description available.'}</small>
                </li>
              ))}
            </ul>
          )}
        </section>

        <section className="detail">
          {!pick ? (
            <p className="muted">Select a result to see the rules.</p>
          ) : (
            <>
              <div className="detail-head">
                <div>
                  <h2>{pick.title}</h2>
                  {pick.source_url && (
                    <a href={pick.source_url} target="_blank" rel="noreferrer" className="muted">
                      Source
                    </a>
                  )}
                </div>
                <button
                  type="button"
                  onClick={summarize}
                  disabled={loading || !!summary}
                  className="secondary"
                >
                  {summary ? 'Summarized' : 'Summarize'}
                </button>
              </div>

              {summary && (
                <div className="summary">
                  <h3>AI Summary</h3>
                  <div className="markdown" style={{ whiteSpace: 'pre-wrap' }}>
                    {summary}
                  </div>
                </div>
              )}

              <div className="summary">
                <h3>Full Rules</h3>
                <div className="markdown" style={{ whiteSpace: 'pre-wrap' }}>
                  {pick.rules_content || 'No rules provided.'}
                </div>
              </div>
            </>
          )}
        </section>
      </div>

      <footer className="muted">© {new Date().getFullYear()} RuleScribe.</footer>
    </div>
  )
}

export default App
