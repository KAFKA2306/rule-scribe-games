import { useMemo } from 'react'

export const GameBackground = ({ games }) => {
  // Use a deterministic shuffle based on content so it's pure (SSR safe) and stable
  const shuffledGames = useMemo(() => {
    if (!games || games.length === 0) return []

    // Minimum tiles needed to cover large screens (e.g. 1920x1080 needs ~150 tiles)
    // We generate 300 to be safe for 4K or ultra-wide
    const list = []
    while (list.length < 300) {
      list.push(...games)
    }

    // Deterministic shuffle with index awareness to separate duplicates
    // Using FNV-1a hash variant for better distribution
    return list
      .map((game, index) => {
        let h = 0x811c9dc5
        const s = `${game.slug}-${index}`
        for (let i = 0; i < s.length; i++) {
          h ^= s.charCodeAt(i)
          h = Math.imul(h, 0x01000193)
        }
        return { game, sort: h >>> 0 }
      })
      .sort((a, b) => a.sort - b.sort)
      .map((item) => item.game)
      .slice(0, 300)
  }, [games])

  if (!games || games.length === 0) return null

  return (
    <div className="game-background-container">
      <div className="game-background-grid">
        {shuffledGames.map((game, index) => (
          <div key={`${game.slug}-${index}`} className="bg-game-tile">
            <img
              src={`/assets/games/${game.slug}.webp`}
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
