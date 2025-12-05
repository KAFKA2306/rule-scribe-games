import { useState } from 'react'

export const RefreshButton = ({ slug, onRefresh }) => {
  const [refreshing, setRefreshing] = useState(false)

  const handleRefresh = async () => {
    setRefreshing(true)
    await fetch(`/api/games/${slug}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ regenerate: true }),
    })
    if (onRefresh) onRefresh()
    setRefreshing(false)
  }

  return (
    <button
      onClick={handleRefresh}
      className="share-btn"
      title="データを更新"
      disabled={refreshing}
      aria-label="Refresh game data"
    >
      {refreshing ? '⏳' : '🔄'}
    </button>
  )
}
