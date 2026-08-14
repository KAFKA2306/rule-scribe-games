import { useEffect, useState } from 'react'

import { useAuth } from '../../auth/authContext'
import { api } from '../../lib/api'

export default function AddToListButton({ game }) {
  const { user, loading: authLoading, signInWithGoogle } = useAuth()
  const [lists, setLists] = useState([])
  const [listId, setListId] = useState('')
  const [status, setStatus] = useState('')
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    if (!user) {
      setLists([])
      setListId('')
      return
    }
    let active = true
    api.get('/api/lists')
      .then((data) => {
        if (!active) return
        const next = data.lists || []
        setLists(next)
        setListId((current) => current || next[0]?.id || '')
      })
      .catch((err) => {
        if (active) setStatus(err.message)
      })
    return () => { active = false }
  }, [user])

  if (authLoading) return null

  if (!user) {
    return (
      <button className="filter-btn" onClick={signInWithGoogle} type="button">
        ログインしてリスト保存
      </button>
    )
  }

  if (lists.length === 0) {
    return <a className="filter-btn" href="/lists">リストを作成</a>
  }

  const add = async () => {
    if (!listId || !game?.id) return
    setBusy(true)
    setStatus('')
    try {
      await api.post(`/api/lists/${listId}/items`, { game_id: game.id })
      setStatus('保存しました')
    } catch (err) {
      setStatus(err.message.includes('already') ? 'すでに追加済みです' : err.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '6px', flexWrap: 'wrap' }}>
      <select
        aria-label="保存先リスト"
        className="sort-select"
        value={listId}
        onChange={(event) => setListId(event.target.value)}
      >
        {lists.map((list) => <option key={list.id} value={list.id}>{list.name}</option>)}
      </select>
      <button className="filter-btn" type="button" disabled={busy} onClick={add}>
        {busy ? '保存中…' : 'リストに保存'}
      </button>
      {status && <span role="status" style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>{status}</span>}
    </div>
  )
}
