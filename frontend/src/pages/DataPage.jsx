import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Helmet } from 'react-helmet-async'
import { api } from '../lib/api'

const PAGE_SIZE = 100

async function fetchAllGames() {
  const games = []
  let total = null

  while (total === null || games.length < total) {
    const response = await api.get(`/api/games?limit=${PAGE_SIZE}&offset=${games.length}`)
    if (!response || !Array.isArray(response.games) || !Number.isInteger(response.total)) {
      throw new Error('ゲーム一覧APIの応答形式を確認できませんでした。')
    }
    if (response.games.length === 0 && games.length < response.total) {
      throw new Error('ゲーム一覧の取得が途中で止まりました。再試行してください。')
    }

    games.push(...response.games)
    total = response.total
  }

  return games
}

function DataPage() {
  const [stats, setStats] = useState(null)
  const [error, setError] = useState(null)
  const [reloadKey, setReloadKey] = useState(0)

  useEffect(() => {
    let cancelled = false
    const loadStats = async () => {
      try {
        const list = await fetchAllGames()
        if (cancelled) return

        const playerCounts = {}
        const playTimes = {}

        list.forEach((game) => {
          const players = `${game.min_players}-${game.max_players}`
          playerCounts[players] = (playerCounts[players] || 0) + 1

          const time = game.play_time || 'Unknown'
          playTimes[time] = (playTimes[time] || 0) + 1
        })

        setStats({
          total: list.length,
          playerCounts: Object.entries(playerCounts)
            .sort((a, b) => b[1] - a[1])
            .slice(0, 10),
          playTimes: Object.entries(playTimes)
            .sort((a, b) => b[1] - a[1])
            .slice(0, 10),
          recentGames: list.slice(0, 10),
        })
      } catch (err) {
        if (cancelled) return
        console.error('Failed to load game data statistics:', err)
        setError('ゲームデータを読み込めませんでした。通信を確認して再試行してください。')
      }
    }
    loadStats()
    return () => {
      cancelled = true
    }
  }, [reloadKey])

  return (
    <div className="app-container">
      <Helmet>
        <title>データ | ボドゲのミカタ</title>
      </Helmet>

      <header className="main-header">
        <Link to="/" className="brand">
          <span className="logo-icon">♜</span>
          <h1>ボドゲのミカタ</h1>
        </Link>
        <nav>
          <span style={{ color: 'var(--accent-primary)' }}>📊 データ</span>
        </nav>
      </header>

      <main style={{ padding: '2rem', maxWidth: '1200px', margin: '0 auto' }}>
        <h2 style={{ marginBottom: '2rem' }}>📊 ゲームデータ統計</h2>

        {error ? (
          <div className="page-state page-state--error" role="alert">
            <p>{error}</p>
            <button
              type="button"
              onClick={() => {
                setError(null)
                setReloadKey((current) => current + 1)
              }}
            >
              再試行
            </button>
          </div>
        ) : !stats ? (
          <div className="spinner" />
        ) : (
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
              gap: '2rem',
            }}
          >
            <div className="stat-card">
              <h3>🎲 総ゲーム数</h3>
              <p style={{ fontSize: '3rem', fontWeight: 700, color: 'var(--accent-primary)' }}>
                {stats.total}
              </p>
            </div>

            <div className="stat-card">
              <h3>👥 プレイ人数別</h3>
              <ul style={{ listStyle: 'none', padding: 0 }}>
                {stats.playerCounts.map(([players, count]) => (
                  <li
                    key={players}
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      padding: '0.5rem 0',
                      borderBottom: '1px solid var(--border-subtle)',
                    }}
                  >
                    <span>{players}人</span>
                    <span style={{ fontWeight: 600 }}>{count}</span>
                  </li>
                ))}
              </ul>
            </div>

            <div className="stat-card">
              <h3>⏱️ プレイ時間別</h3>
              <ul style={{ listStyle: 'none', padding: 0 }}>
                {stats.playTimes.map(([time, count]) => (
                  <li
                    key={time}
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      padding: '0.5rem 0',
                      borderBottom: '1px solid var(--border-subtle)',
                    }}
                  >
                    <span>{time}分</span>
                    <span style={{ fontWeight: 600 }}>{count}</span>
                  </li>
                ))}
              </ul>
            </div>

            <div className="stat-card" style={{ gridColumn: '1 / -1' }}>
              <h3>🆕 最新ゲーム</h3>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
                {stats.recentGames.map((game) => (
                  <Link
                    key={game.slug}
                    to={`/?q=${encodeURIComponent(game.title_ja)}`}
                    style={{
                      padding: '0.5rem 1rem',
                      background: 'var(--bg-tertiary)',
                      borderRadius: '0.5rem',
                      color: 'var(--text-primary)',
                      textDecoration: 'none',
                    }}
                  >
                    {game.title_ja}
                  </Link>
                ))}
              </div>
            </div>
          </div>
        )}
      </main>

      <footer className="main-footer">© {new Date().getFullYear()} ボドゲのミカタ</footer>
    </div>
  )
}

export default DataPage
