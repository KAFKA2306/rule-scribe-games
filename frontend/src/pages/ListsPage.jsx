import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

import { useAuth } from '../auth/authContext'
import { api } from '../lib/api'

export default function ListsPage() {
  const { user, loading: authLoading, signInWithGoogle } = useAuth()
  const [lists, setLists] = useState([])
  const [selectedId, setSelectedId] = useState('')
  const [detail, setDetail] = useState(null)
  const [newName, setNewName] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const loadLists = async (preferredId = '') => {
    setLoading(true)
    setError('')
    try {
      const data = await api.get('/api/lists')
      const next = data.lists || []
      setLists(next)
      const nextId = preferredId || selectedId || next[0]?.id || ''
      setSelectedId(nextId)
      if (nextId) {
        setDetail(await api.get(`/api/lists/${nextId}`))
      } else {
        setDetail(null)
      }
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (user) loadLists()
    else {
      setLists([])
      setSelectedId('')
      setDetail(null)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user])

  const selectList = async (id) => {
    setSelectedId(id)
    setLoading(true)
    setError('')
    try {
      setDetail(await api.get(`/api/lists/${id}`))
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const createList = async (event) => {
    event.preventDefault()
    const name = newName.trim()
    if (!name) return
    setError('')
    try {
      const created = await api.post('/api/lists', { name, visibility: 'private' })
      setNewName('')
      await loadLists(created.id)
    } catch (err) {
      setError(err.message)
    }
  }

  const renameList = async () => {
    if (!detail) return
    const name = window.prompt('新しいリスト名', detail.name)?.trim()
    if (!name || name === detail.name) return
    try {
      await api.patch(`/api/lists/${detail.id}`, { name })
      await loadLists(detail.id)
    } catch (err) {
      setError(err.message)
    }
  }

  const deleteList = async () => {
    if (!detail || !window.confirm(`「${detail.name}」を削除しますか？`)) return
    try {
      await api.delete(`/api/lists/${detail.id}`)
      setSelectedId('')
      setDetail(null)
      await loadLists()
    } catch (err) {
      setError(err.message)
    }
  }

  const removeItem = async (itemId) => {
    if (!detail) return
    try {
      await api.delete(`/api/lists/${detail.id}/items/${itemId}`)
      await selectList(detail.id)
    } catch (err) {
      setError(err.message)
    }
  }

  const moveItem = async (index, delta) => {
    if (!detail) return
    const nextIndex = index + delta
    if (nextIndex < 0 || nextIndex >= detail.items.length) return
    const items = [...detail.items]
    ;[items[index], items[nextIndex]] = [items[nextIndex], items[index]]
    setDetail({ ...detail, items })
    try {
      await api.put(`/api/lists/${detail.id}/order`, { item_ids: items.map((item) => item.id) })
    } catch (err) {
      setError(err.message)
      await selectList(detail.id)
    }
  }

  if (authLoading) return <main style={{ padding: '3rem' }}>認証状態を確認しています…</main>

  if (!user) {
    return (
      <main style={{ maxWidth: '720px', margin: '0 auto', padding: '3rem 1rem' }}>
        <Link to="/" className="back-link">← DIRECTORY</Link>
        <h1>マイリスト</h1>
        <p>リストの作成・保存にはログインが必要です。</p>
        <button type="button" className="filter-btn active" onClick={signInWithGoogle}>Googleでログイン</button>
      </main>
    )
  }

  return (
    <main style={{ maxWidth: '1100px', margin: '0 auto', padding: '2rem 1rem' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', flexWrap: 'wrap', marginBottom: '1.5rem' }}>
        <Link to="/" className="back-link">← DIRECTORY</Link>
        <h1 style={{ margin: 0 }}>マイリスト</h1>
      </div>

      <form onSubmit={createList} style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', marginBottom: '1.5rem' }}>
        <input
          className="search-input"
          style={{ maxWidth: '360px' }}
          value={newName}
          maxLength={80}
          onChange={(event) => setNewName(event.target.value)}
          placeholder="新しいリスト名"
          aria-label="新しいリスト名"
        />
        <button className="filter-btn" type="submit">リストを作成</button>
      </form>

      {error && <div role="alert" style={{ marginBottom: '1rem', color: '#ff7777' }}>{error}</div>}
      {loading && <div style={{ marginBottom: '1rem', color: 'var(--text-secondary)' }}>読み込み中…</div>}

      {lists.length === 0 && !loading ? (
        <div className="pro-card">まだリストがありません。最初のリストを作成してください。</div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'minmax(180px, 260px) minmax(0, 1fr)', gap: '16px' }}>
          <aside style={{ position: 'static', width: 'auto', height: 'auto' }}>
            {lists.map((list) => (
              <button
                type="button"
                key={list.id}
                className={`filter-btn ${selectedId === list.id ? 'active' : ''}`}
                style={{ width: '100%', marginBottom: '8px', textAlign: 'left' }}
                onClick={() => selectList(list.id)}
              >
                {list.name}
              </button>
            ))}
          </aside>

          <section>
            {detail && (
              <>
                <div style={{ display: 'flex', gap: '8px', alignItems: 'center', flexWrap: 'wrap', marginBottom: '1rem' }}>
                  <h2 style={{ margin: 0 }}>{detail.name}</h2>
                  <button type="button" className="filter-btn" onClick={renameList}>名前変更</button>
                  <button type="button" className="filter-btn" onClick={deleteList}>削除</button>
                </div>

                {detail.items.length === 0 ? (
                  <div className="pro-card">このリストは空です。ゲーム詳細から追加できます。</div>
                ) : detail.items.map((item, index) => {
                  const title = item.game?.title_ja || item.game?.title || item.game_title_snapshot
                  return (
                    <div key={item.id} className="pro-card" style={{ display: 'flex', gap: '12px', alignItems: 'center', marginBottom: '10px', flexWrap: 'wrap' }}>
                      <div style={{ flex: '1 1 220px' }}>
                        {item.game ? <Link to={`/games/${item.game.slug}`}>{title}</Link> : <strong>{title}</strong>}
                        {item.unavailable && <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>現在利用できないゲーム</div>}
                      </div>
                      <div style={{ display: 'flex', gap: '6px' }}>
                        <button type="button" className="filter-btn" aria-label={`${title}を上へ`} disabled={index === 0} onClick={() => moveItem(index, -1)}>↑</button>
                        <button type="button" className="filter-btn" aria-label={`${title}を下へ`} disabled={index === detail.items.length - 1} onClick={() => moveItem(index, 1)}>↓</button>
                        <button type="button" className="filter-btn" onClick={() => removeItem(item.id)}>削除</button>
                      </div>
                    </div>
                  )
                })}
              </>
            )}
          </section>
        </div>
      )}

      <style>{`@media (max-width: 720px) { main > div[style*="grid-template-columns"] { grid-template-columns: 1fr !important; } }`}</style>
    </main>
  )
}
