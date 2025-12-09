import { useMemo } from 'react'

export const GameBackground = ({ games }) => {
  // Shuffle games to make the background look more interesting/random
  // Memoize so it doesn't reshuffle on every render
  const shuffledGames = useMemo(() => {
    if (!games || games.length === 0) return []
    // Create a copy and shuffle
    const list = [...games]
    // If we have few games, duplicate them to fill the screen
    if (list.length < 50) {
      while (list.length < 50) {
        list.push(...games)
      }
    }
    
    // Simple shuffle
    for (let i = list.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1))
      ;[list[i], list[j]] = [list[j], list[i]]
    }
    return list.slice(0, 80) // Limit to a reasonable number to cover screen
  }, [games])

  if (!games || games.length === 0) return null

  return (
    <div className="game-background-container">
      <div className="game-background-grid">
        {shuffledGames.map((game, index) => (
          <div 
            key={`${game.slug}-${index}`} 
            className="bg-game-tile"
          >
            <img 
              src={`/assets/games/${game.slug}.png`}
              alt=""
              loading="lazy"
              onError={(e) => e.target.style.opacity = 0}
            />
          </div>
        ))}
      </div>
      <div className="game-background-overlay" />
    </div>
  )
}
