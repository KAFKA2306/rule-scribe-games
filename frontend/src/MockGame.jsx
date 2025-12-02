import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

function MockGame() {
  const [cards, setCards] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [gameStatus, setGameStatus] = useState('idle') // idle, won

  useEffect(() => {
    const loadData = async () => {
      try {
        // Fetch games to get card data. For now, we'll just take the first game that has cards.
        const res = await fetch('/api/games?limit=10')
        if (!res.ok) throw new Error(await res.text())
        const games = await res.json()
        
        // Find a game with popular_cards
        const gameWithCards = games.find(g => g.structured_data?.popular_cards?.length > 0)
        
        if (gameWithCards) {
          setCards(gameWithCards.structured_data.popular_cards)
        } else {
          setError('カードデータを持つゲームが見つかりませんでした。')
        }
      } catch (err) {
        console.error(err)
        setError('データの読み込みに失敗しました')
      } finally {
        setLoading(false)
      }
    }
    loadData()
  }, [])

  const handleSimulate = () => {
    setGameStatus('won')
  }

  const handleReset = () => {
    setGameStatus('idle')
  }

  return (
    <div className="mock-game-page">
      <header className="app-header">
        <div className="header-content">
          <h1>🃏 Mock Game Card List</h1>
          <Link to="/" className="back-link">← Home</Link>
        </div>
      </header>

      <main className="container">
        {loading && <p className="loading">Loading cards...</p>}
        {error && <p className="error">{error}</p>}

        {!loading && !error && (
          <>
            <div className="controls">
              {gameStatus === 'idle' ? (
                <button onClick={handleSimulate} className="simulate-btn">
                  Simulate Game
                </button>
              ) : (
                <div className="victory-message">
                  <h2>🎉 Everyone Wins! 🎉</h2>
                  <p>Congratulations! You are all winners in this mock mode.</p>
                  <button onClick={handleReset} className="reset-btn">
                    Play Again
                  </button>
                </div>
              )}
            </div>

            <div className="card-grid">
              {cards.map((card, index) => (
                <div key={index} className="game-card">
                  <div className="card-inner">
                    <div className="card-top">
                      <span className="card-cost">{card.cost || '?'}</span>
                      <h3 className="card-title">{card.name}</h3>
                    </div>
                    <div className="card-type">{card.type}</div>
                    <div className="card-body">
                      <p>{card.reason || 'No description available.'}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </>
        )}
        
        {!loading && !error && cards.length === 0 && (
           <p>No cards found.</p>
        )}
      </main>

      <style>{`
        .mock-game-page {
          min-height: 100vh;
          background: #f0f2f5;
          font-family: 'Inter', sans-serif;
          color: #333;
        }
        .app-header {
          background: #fff;
          padding: 1rem 2rem;
          box-shadow: 0 2px 4px rgba(0,0,0,0.05);
          margin-bottom: 2rem;
        }
        .header-content {
          max-width: 1200px;
          margin: 0 auto;
          display: flex;
          justify-content: space-between;
          align-items: center;
        }
        .header-content h1 {
          margin: 0;
          font-size: 1.5rem;
          color: #1a1a1a;
        }
        .back-link {
          text-decoration: none;
          color: #666;
          font-weight: 500;
        }
        .back-link:hover {
          color: #000;
        }
        .container {
          max-width: 1200px;
          margin: 0 auto;
          padding: 0 2rem 2rem;
        }
        .controls {
          margin-bottom: 2rem;
          text-align: center;
        }
        .simulate-btn {
          background: #10b981;
          color: white;
          border: none;
          padding: 0.75rem 1.5rem;
          font-size: 1.1rem;
          border-radius: 8px;
          cursor: pointer;
          font-weight: 600;
          transition: background 0.2s;
        }
        .simulate-btn:hover {
          background: #059669;
        }
        .victory-message {
          background: #ecfdf5;
          border: 2px solid #10b981;
          border-radius: 12px;
          padding: 2rem;
          text-align: center;
          animation: popIn 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        }
        .victory-message h2 {
          color: #047857;
          margin-top: 0;
          font-size: 2rem;
        }
        .victory-message p {
          color: #065f46;
          font-size: 1.2rem;
          margin-bottom: 1.5rem;
        }
        .reset-btn {
          background: #fff;
          color: #10b981;
          border: 2px solid #10b981;
          padding: 0.5rem 1rem;
          font-size: 1rem;
          border-radius: 6px;
          cursor: pointer;
          font-weight: 600;
          transition: all 0.2s;
        }
        .reset-btn:hover {
          background: #10b981;
          color: white;
        }
        @keyframes popIn {
          from { opacity: 0; transform: scale(0.8); }
          to { opacity: 1; transform: scale(1); }
        }
        .card-grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
          gap: 1.5rem;
        }
        .game-card {
          background: #fff;
          border-radius: 12px;
          overflow: hidden;
          box-shadow: 0 4px 6px rgba(0,0,0,0.05);
          transition: transform 0.2s, box-shadow 0.2s;
          border: 1px solid #eee;
        }
        .game-card:hover {
          transform: translateY(-4px);
          box-shadow: 0 10px 15px rgba(0,0,0,0.1);
        }
        .card-inner {
          padding: 1.5rem;
          display: flex;
          flex-direction: column;
          height: 100%;
        }
        .card-top {
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
          margin-bottom: 0.5rem;
        }
        .card-cost {
          background: #2563eb;
          color: white;
          width: 28px;
          height: 28px;
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          font-weight: bold;
          font-size: 0.9rem;
          flex-shrink: 0;
          margin-right: 0.75rem;
        }
        .card-title {
          margin: 0;
          font-size: 1.1rem;
          line-height: 1.4;
          flex-grow: 1;
        }
        .card-type {
          font-size: 0.8rem;
          color: #666;
          text-transform: uppercase;
          letter-spacing: 0.05em;
          margin-bottom: 1rem;
          font-weight: 600;
        }
        .card-body {
          font-size: 0.95rem;
          line-height: 1.6;
          color: #444;
        }
        .loading, .error {
          text-align: center;
          padding: 2rem;
          font-size: 1.1rem;
        }
        .error {
          color: #dc2626;
        }
      `}</style>
    </div>
  )
}

export default MockGame
