import { useState } from 'react'
import { api } from '../../lib/api'

export const RegenerateButton = ({ title, onRegenerate }) => {
  const [regenerating, setRegenerating] = useState(false)

  const handleRegenerate = async () => {
    setRegenerating(true)
    try {
      const data = await api.post('/api/search', { query: title, generate: true })
      if (onRegenerate && Array.isArray(data) && data[0]) {
        onRegenerate(data[0])
      }
    } catch (err) {
      console.error('Regeneration failed:', err)
      alert('再生成に失敗しました')
    } finally {
      setRegenerating(false)
    }
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
