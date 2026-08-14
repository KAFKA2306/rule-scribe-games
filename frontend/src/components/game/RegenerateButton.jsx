import { useState } from 'react'
import { api } from '../../lib/api'

export const RegenerateButton = ({ slug, onRegenerate }) => {
  const [regenerating, setRegenerating] = useState(false)

  const handleRegenerate = async () => {
    if (!slug) return

    setRegenerating(true)
    try {
      const data = await api.patch(`/api/games/${encodeURIComponent(slug)}?regenerate=true&fill_missing_only=true`)
      if (onRegenerate && data?.id) {
        onRegenerate(data)
      }
    } catch (err) {
      console.error('Regeneration failed:', err)
      const message = err?.status === 401
        ? '再生成にはログインが必要です'
        : '再生成に失敗しました'
      alert(message)
    } finally {
      setRegenerating(false)
    }
  }

  return (
    <button
      onClick={handleRegenerate}
      className="share-btn"
      title="AIで不足情報を再生成"
      disabled={regenerating || !slug}
      aria-label="Regenerate missing game data with AI"
    >
      {regenerating ? '⏳ 生成中' : '✨ 再生成'}
    </button>
  )
}
