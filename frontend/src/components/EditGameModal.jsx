import { useEffect, useRef, useState } from 'react'

function initialFormData(game) {
  if (!game) return {}
  let structuredData = { keywords: [] }
  if (game.structured_data && !Array.isArray(game.structured_data)) {
    structuredData = { ...game.structured_data }
    if (!structuredData.keywords) structuredData.keywords = []
  }
  return {
    title: game.title || '',
    title_ja: game.title_ja || '',
    description: game.description || '',
    summary: game.summary || '',
    rules_content: game.rules_content || '',
    min_players: game.min_players || '',
    max_players: game.max_players || '',
    play_time: game.play_time || '',
    min_age: game.min_age || '',
    published_year: game.published_year || '',
    image_url: game.image_url || '',
    official_url: game.official_url || '',
    bgg_url: game.bgg_url || '',
    structured_data: structuredData,
  }
}

function focusableElements(container) {
  if (!container) return []
  return [...container.querySelectorAll(
    'button:not([disabled]), input:not([disabled]), textarea:not([disabled]), select:not([disabled]), a[href], [tabindex]:not([tabindex="-1"])',
  )].filter((element) => !element.hidden && element.getAttribute('aria-hidden') !== 'true')
}

export default function EditGameModal({ game, isOpen, onClose, onSave }) {
  const [formData, setFormData] = useState(() => initialFormData(game))
  const [saving, setSaving] = useState(false)
  const [newKeyword, setNewKeyword] = useState({ term: '', description: '' })
  const dialogRef = useRef(null)
  const previousFocusRef = useRef(null)

  useEffect(() => {
    if (isOpen) setFormData(initialFormData(game))
  }, [game, isOpen])

  useEffect(() => {
    if (!isOpen) return undefined
    previousFocusRef.current = document.activeElement
    const frame = window.requestAnimationFrame(() => {
      const firstField = dialogRef.current?.querySelector('#edit-game-title')
      if (firstField) firstField.focus()
      else dialogRef.current?.focus()
    })

    return () => {
      window.cancelAnimationFrame(frame)
      const previous = previousFocusRef.current
      if (previous instanceof HTMLElement && previous.isConnected) previous.focus()
    }
  }, [isOpen])

  const handleChange = (event) => {
    const { name, value } = event.target
    setFormData((previous) => ({ ...previous, [name]: value }))
  }

  const handleAddKeyword = () => {
    if (!newKeyword.term.trim()) return
    setFormData((previous) => ({
      ...previous,
      structured_data: {
        ...previous.structured_data,
        keywords: [...(previous.structured_data?.keywords || []), newKeyword],
      },
    }))
    setNewKeyword({ term: '', description: '' })
  }

  const handleRemoveKeyword = (index) => {
    setFormData((previous) => {
      const keywords = [...(previous.structured_data?.keywords || [])]
      keywords.splice(index, 1)
      return {
        ...previous,
        structured_data: { ...previous.structured_data, keywords },
      }
    })
  }

  const handleSubmit = async (event) => {
    event.preventDefault()
    setSaving(true)
    const payload = { ...formData }
    const numericFields = ['min_players', 'max_players', 'play_time', 'min_age', 'published_year']

    numericFields.forEach((field) => {
      if (payload[field] === '') payload[field] = null
      else payload[field] = Number(payload[field])
    })

    try {
      await onSave(payload)
      onClose()
    } finally {
      setSaving(false)
    }
  }

  const handleDialogKeyDown = (event) => {
    if (event.key === 'Escape') {
      event.preventDefault()
      if (!saving) onClose()
      return
    }
    if (event.key !== 'Tab') return

    const focusable = focusableElements(dialogRef.current)
    if (focusable.length === 0) {
      event.preventDefault()
      dialogRef.current?.focus()
      return
    }

    const first = focusable[0]
    const last = focusable[focusable.length - 1]
    if (event.shiftKey && document.activeElement === first) {
      event.preventDefault()
      last.focus()
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault()
      first.focus()
    }
  }

  if (!isOpen) return null

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div
        ref={dialogRef}
        className="modal-content"
        role="dialog"
        aria-modal="true"
        aria-labelledby="edit-game-dialog-title"
        tabIndex={-1}
        onClick={(event) => event.stopPropagation()}
        onKeyDown={handleDialogKeyDown}
      >
        <div className="modal-header">
          <h3 id="edit-game-dialog-title">ゲーム情報を編集</h3>
          <button type="button" className="close-btn" onClick={onClose} aria-label="編集画面を閉じる" disabled={saving}>
            &times;
          </button>
        </div>

        <form onSubmit={handleSubmit} className="edit-form">
          <div className="form-group">
            <label htmlFor="edit-game-title">タイトル (英語/原題)</label>
            <input id="edit-game-title" name="title" value={formData.title || ''} onChange={handleChange} required />
          </div>

          <div className="form-group">
            <label htmlFor="edit-game-title-ja">タイトル (日本語)</label>
            <input id="edit-game-title-ja" name="title_ja" value={formData.title_ja || ''} onChange={handleChange} />
          </div>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="edit-game-min-players">最小人数</label>
              <input id="edit-game-min-players" type="number" name="min_players" value={formData.min_players ?? ''} onChange={handleChange} />
            </div>
            <div className="form-group">
              <label htmlFor="edit-game-max-players">最大人数</label>
              <input id="edit-game-max-players" type="number" name="max_players" value={formData.max_players ?? ''} onChange={handleChange} />
            </div>
            <div className="form-group">
              <label htmlFor="edit-game-play-time">プレイ時間(分)</label>
              <input id="edit-game-play-time" type="number" name="play_time" value={formData.play_time ?? ''} onChange={handleChange} />
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="edit-game-min-age">対象年齢</label>
              <input id="edit-game-min-age" type="number" name="min_age" value={formData.min_age ?? ''} onChange={handleChange} />
            </div>
            <div className="form-group">
              <label htmlFor="edit-game-year">発行年</label>
              <input id="edit-game-year" type="number" name="published_year" value={formData.published_year ?? ''} onChange={handleChange} />
            </div>
          </div>

          <div className="form-group">
            <label htmlFor="edit-game-summary">概要 (Summary)</label>
            <textarea id="edit-game-summary" name="summary" value={formData.summary || ''} onChange={handleChange} rows={3} />
          </div>

          <div className="form-group">
            <label htmlFor="edit-game-description">詳細説明 (Description)</label>
            <textarea id="edit-game-description" name="description" value={formData.description || ''} onChange={handleChange} rows={5} />
          </div>

          <div className="form-group">
            <label htmlFor="edit-game-rules">ルール詳細 (Rules Content Markdown)</label>
            <textarea id="edit-game-rules" name="rules_content" value={formData.rules_content || ''} onChange={handleChange} rows={8} />
          </div>

          <fieldset className="form-group keyword-fieldset">
            <legend>キーワード (Keywords)</legend>
            <div className="keyword-list">
              {(formData.structured_data?.keywords || []).map((keyword, index) => (
                <div key={`${keyword.term}-${index}`} className="keyword-row">
                  <input readOnly value={keyword.term} aria-label={`キーワード ${index + 1} の用語`} className="keyword-term" />
                  <input readOnly value={keyword.description} aria-label={`キーワード ${index + 1} の説明`} className="keyword-description" />
                  <button
                    type="button"
                    onClick={() => handleRemoveKeyword(index)}
                    className="keyword-remove-button"
                    aria-label={`${keyword.term || 'キーワード'}を削除`}
                  >
                    ×
                  </button>
                </div>
              ))}
            </div>
            <div className="keyword-row keyword-row--new">
              <label className="sr-only" htmlFor="edit-game-new-keyword">追加するキーワード</label>
              <input
                id="edit-game-new-keyword"
                placeholder="用語 (例: デッキ構築)"
                value={newKeyword.term}
                onChange={(event) => setNewKeyword({ ...newKeyword, term: event.target.value })}
                className="keyword-term"
              />
              <label className="sr-only" htmlFor="edit-game-new-keyword-description">追加するキーワードの説明</label>
              <input
                id="edit-game-new-keyword-description"
                placeholder="説明"
                value={newKeyword.description}
                onChange={(event) => setNewKeyword({ ...newKeyword, description: event.target.value })}
                className="keyword-description"
              />
              <button type="button" onClick={handleAddKeyword} className="btn-secondary keyword-add-button" disabled={!newKeyword.term.trim()}>
                追加
              </button>
            </div>
          </fieldset>

          <div className="form-group">
            <label htmlFor="edit-game-image-url">画像URL</label>
            <input id="edit-game-image-url" name="image_url" value={formData.image_url || ''} onChange={handleChange} />
          </div>

          <div className="form-group">
            <label htmlFor="edit-game-official-url">公式サイトURL</label>
            <input id="edit-game-official-url" name="official_url" value={formData.official_url || ''} onChange={handleChange} />
          </div>

          <div className="form-group">
            <label htmlFor="edit-game-bgg-url">BGG URL</label>
            <input id="edit-game-bgg-url" name="bgg_url" value={formData.bgg_url || ''} onChange={handleChange} />
          </div>

          <div className="modal-actions">
            <button type="button" onClick={onClose} className="btn-secondary" disabled={saving}>キャンセル</button>
            <button type="submit" className="btn-primary" disabled={saving}>{saving ? '保存中...' : '保存'}</button>
          </div>
        </form>
      </div>
    </div>
  )
}