import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

function DataViewer() {
  const [games, setGames] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    const loadData = async () => {
      const res = await fetch('/api/games?limit=200')
      if (!res.ok) throw new Error(await res.text())
      const data = await res.json()
      setGames(data)
      setLoading(false)
    }
    loadData()
  }, [])

  return (
    <div className="data-viewer">
      <header className="data-header">
        <div>
          <h1>📊 Database Viewer</h1>
          <p className="muted">Supabase games テーブルの全データ</p>
        </div>
        <Link to="/" className="back-link">
          ← ホームに戻る
        </Link>
      </header>

      {loading && <p className="loading">読み込み中...</p>}
      {error && <p className="error">{error}</p>}

      <div className="data-grid">
        {games.map((game) => (
          <div key={game.id} className="data-card">
            <div className="card-header">
              <h3>{game.title}</h3>
              <span className="card-id">ID: {game.id}</span>
            </div>

            {game.description && (
              <p className="card-description">{game.description}</p>
            )}

            <div className="card-meta">
              {game.source_url && (
                <div className="meta-item">
                  <strong>Source:</strong>
                  <a
                    href={game.source_url}
                    target="_blank"
                    rel="noreferrer"
                    className="source-link"
                  >
                    {game.source_url.length > 50
                      ? game.source_url.substring(0, 50) + '...'
                      : game.source_url}
                  </a>
                </div>
              )}

              {game.structured_data && (
                <div className="meta-item">
                  <strong>Structured Data:</strong>
                  <details>
                    <summary>表示</summary>
                    <pre className="json-preview">
                      {JSON.stringify(game.structured_data, null, 2)}
                    </pre>
                  </details>
                </div>
              )}

              {game.data_version && (
                <div className="meta-item">
                  <strong>Data Version:</strong> {game.data_version}
                </div>
              )}

              <div className="meta-item">
                <strong>Created:</strong>{' '}
                {new Date(game.created_at).toLocaleString('ja-JP')}
              </div>

              <div className="meta-item">
                <strong>Updated:</strong>{' '}
                {new Date(game.updated_at).toLocaleString('ja-JP')}
              </div>
            </div>
          </div>
        ))}
      </div>

      {!loading && games.length === 0 && (
        <p className="empty-state">データがありません</p>
      )}
    </div>
  )
}

export default DataViewer
