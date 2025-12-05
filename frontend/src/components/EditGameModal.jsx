import { useState, useEffect } from 'react'

export default function EditGameModal({ game, isOpen, onClose, onSave }) {
  const [formData, setFormData] = useState({})
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    if (game) {
      setFormData({
        title: game.title || '',
        title_ja: game.title_ja || '',
        description: game.description || '',
        summary: game.summary || '',
        min_players: game.min_players || '',
        max_players: game.max_players || '',
        play_time: game.play_time || '',
        min_age: game.min_age || '',
        published_year: game.published_year || '',
        image_url: game.image_url || '',
        official_url: game.official_url || '',
        bgg_url: game.bgg_url || '',
      })
    }
  }, [game])

  const handleChange = (e) => {
    const { name, value } = e.target
    setFormData((prev) => ({ ...prev, [name]: value }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setSaving(true)
    try {
      const payload = { ...formData }
      const numericFields = ['min_players', 'max_players', 'play_time', 'min_age', 'published_year']

      numericFields.forEach((field) => {
        if (payload[field] === '') payload[field] = null
        else payload[field] = Number(payload[field])
      })

      await onSave(payload)
      onClose()
    } catch (error) {
      console.error('Save failed:', error)
      alert('保存に失敗しました')
    } finally {
      setSaving(false)
    }
  }

  if (!isOpen) return null

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h3>ゲーム情報を編集</h3>
          <button className="close-btn" onClick={onClose}>
            &times;
          </button>
        </div>

        <form onSubmit={handleSubmit} className="edit-form">
          <div className="form-group">
            <label>タイトル (英語/原題)</label>
            <input name="title" value={formData.title} onChange={handleChange} required />
          </div>

          <div className="form-group">
            <label>タイトル (日本語)</label>
            <input name="title_ja" value={formData.title_ja} onChange={handleChange} />
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>最小人数</label>
              <input
                type="number"
                name="min_players"
                value={formData.min_players}
                onChange={handleChange}
              />
            </div>
            <div className="form-group">
              <label>最大人数</label>
              <input
                type="number"
                name="max_players"
                value={formData.max_players}
                onChange={handleChange}
              />
            </div>
            <div className="form-group">
              <label>プレイ時間(分)</label>
              <input
                type="number"
                name="play_time"
                value={formData.play_time}
                onChange={handleChange}
              />
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>対象年齢</label>
              <input
                type="number"
                name="min_age"
                value={formData.min_age}
                onChange={handleChange}
              />
            </div>
            <div className="form-group">
              <label>発行年</label>
              <input
                type="number"
                name="published_year"
                value={formData.published_year}
                onChange={handleChange}
              />
            </div>
          </div>

          <div className="form-group">
            <label>概要 (Summary)</label>
            <textarea name="summary" value={formData.summary} onChange={handleChange} rows={3} />
          </div>

          <div className="form-group">
            <label>詳細説明 (Description)</label>
            <textarea
              name="description"
              value={formData.description}
              onChange={handleChange}
              rows={5}
            />
          </div>

          <div className="form-group">
            <label>画像URL</label>
            <input name="image_url" value={formData.image_url} onChange={handleChange} />
          </div>

          <div className="form-group">
            <label>公式サイトURL</label>
            <input name="official_url" value={formData.official_url} onChange={handleChange} />
          </div>

          <div className="form-group">
            <label>BGG URL</label>
            <input name="bgg_url" value={formData.bgg_url} onChange={handleChange} />
          </div>

          <div className="modal-actions">
            <button type="button" onClick={onClose} className="btn-secondary" disabled={saving}>
              キャンセル
            </button>
            <button type="submit" className="btn-primary" disabled={saving}>
              {saving ? '保存中...' : '保存'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
