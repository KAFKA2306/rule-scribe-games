import { useMemo } from 'react'

export const GameBackground = ({ games }) => {
  // Use a deterministic shuffle based on content so it's pure (SSR safe) and stable
  const shuffledGames = useMemo(() => {
    if (!games || games.length === 0) return []

    const list = [...games]
    if (list.length < 50) {
      while (list.length < 50) {
        list.push(...games)
      }
    }

    // Sort pseudo-randomly based on string hash
    list.sort((a, b) => {
      const hashA = a.slug.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0)
      const hashB = b.slug.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0)
      return (hashA % 100) - (hashB % 100)
    })

    return list.slice(0, 80)
  }, [games])

  if (!games || games.length === 0) return null

  return (
    <div className="game-background-container">
      <div className="game-background-grid">
        {shuffledGames.map((game, index) => (
          <div key={`${game.slug}-${index}`} className="bg-game-tile">
            <img
              src={`/assets/games/${game.slug}.png`}
              alt=""
              loading="lazy"
              onError={(e) => (e.target.style.opacity = 0)}
            />
          </div>
        ))}
      </div>
      <div className="game-background-overlay" />
    </div>
  )
}
