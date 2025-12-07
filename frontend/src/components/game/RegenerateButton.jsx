import { useState } from 'react'

export const RegenerateButton = ({ title, onRegenerate }) => {
  const [regenerating, setRegenerating] = useState(false)

  const handleRegenerate = async () => {
    setRegenerating(true)
    const res = await fetch('/api/search', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query: title, generate: true }),
    })
    const data = await res.json()
    if (onRegenerate && Array.isArray(data) && data[0]) {
      onRegenerate(data[0])
    }
    setRegenerating(false)
  }

  return (
    <button
      onClick={handleRegenerate}
      className="share-btn"
      title="AIで再生成"
      disabled={regenerating}
      aria-label="Regenerate game data with AI"
    >
      {regenerating ? '⏳ 生成中' : '✨ 再生成'}
    </button>
  )
}
