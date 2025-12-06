import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Helmet } from 'react-helmet-async'
import { api } from '../lib/api'

function DataPage() {
  const [stats, setStats] = useState(null)

  useEffect(() => {
    const loadStats = async () => {
      const games = await api.get('/api/games?limit=1000')
      const list = Array.isArray(games) ? games : games.games || []

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
    }
    loadStats()
  }, [])

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

        {!stats ? (
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
