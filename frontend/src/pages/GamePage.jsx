import { useParams } from 'react-router-dom'
import { useEffect, useState } from 'react'
import ReactMarkdown from 'react-markdown'

export default function GamePage() {
  const { slug } = useParams()
  const [game, setGame] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function fetchGame() {
      setLoading(true)
      try {
        const res = await fetch(`/api/games/${slug}`)
        if (res.ok) {
          const data = await res.json()
          setGame(data)
        } else {
          setGame(null)
        }
      } catch (e) {
        console.error('Failed to fetch game:', e)
        setGame(null)
      } finally {
        setLoading(false)
      }
    }
    fetchGame()
  }, [slug])

  if (loading) return <div className="p-4">Loading...</div>
  if (!game) return <div className="p-4">Game not found</div>

  return (
    <div className="app">
      <header>
        <div className="brand">
          <a href="/">ボドゲのミカタ</a>
        </div>
        <span className="muted">ルール、わからなくなっても大丈夫。</span>
        <a href="/data" className="data-link">
          📊 データ
        </a>
      </header>

      <div className="layout">
        <section
          className="detail panel"
          style={{ width: '100%', maxWidth: '800px', margin: '0 auto' }}
        >
          <div className="detail-head">
            <div>
              <h2>{game.title}</h2>
              {game.source_url && (
                <a href={game.source_url} target="_blank" rel="noreferrer" className="muted">
                  情報元
                </a>
              )}
            </div>
          </div>

          {game.structured_data?.keywords && (
            <div className="summary">
              <h3>キーワード</h3>
              {game.structured_data.keywords.map((kw) => (
                <div key={kw.term} style={{ marginBottom: '8px' }}>
                  <strong>{kw.term}</strong>: {kw.description}
                </div>
              ))}
            </div>
          )}

          {game.structured_data?.popular_cards && (
            <div className="summary">
              <h3>人気のカード/コンポーネント</h3>
              {game.structured_data.popular_cards.map((card) => (
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
              {game.rules_content || 'ルールが見つかりませんでした。'}
            </ReactMarkdown>
          </div>
        </section>
      </div>

      <footer className="muted">© {new Date().getFullYear()} ボドゲのミカタ</footer>
    </div>
  )
}
