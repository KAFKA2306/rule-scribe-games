import { useEffect, useState } from 'react'

import { useAuth } from '../../auth/authContext'
import { api } from '../../lib/api'

export default function OwnedGameButton({ game }) {
  const { user, loading: authLoading, signInWithGoogle } = useAuth()
  const [owned, setOwned] = useState(false)
  const [checking, setChecking] = useState(false)
  const [busy, setBusy] = useState(false)
  const [status, setStatus] = useState('')

  useEffect(() => {
    if (!user || !game?.id) {
      setOwned(false)
      setChecking(false)
      setStatus('')
      return
    }

    let active = true
    setChecking(true)
    setStatus('')
    api.get(`/api/owned-games/${game.id}`)
      .then((data) => {
        if (active) setOwned(Boolean(data.owned))
      })
      .catch((err) => {
        if (active) setStatus(err.message)
      })
      .finally(() => {
        if (active) setChecking(false)
      })

    return () => { active = false }
  }, [user, game?.id])

  if (authLoading) return null

  if (!user) {
    return (
      <button className="filter-btn" onClick={signInWithGoogle} type="button">
        ログインして所持登録
      </button>
    )
  }

  const toggleOwned = async () => {
    if (!game?.id || checking || busy) return
    setBusy(true)
    setStatus('')
    try {
      if (owned) {
        const data = await api.delete(`/api/owned-games/${game.id}`)
        setOwned(Boolean(data.owned))
        setStatus('所持ゲームから解除しました')
      } else {
        const data = await api.put(`/api/owned-games/${game.id}`, {})
        setOwned(Boolean(data.owned))
        setStatus(data.created ? '所持ゲームに登録しました' : '所持登録済みです')
      }
    } catch (err) {
      setStatus(err.message)
    } finally {
      setBusy(false)
    }
  }

  const label = checking
    ? '所持状態を確認中…'
    : busy
      ? '更新中…'
      : owned
        ? '✓ 所持しています'
        : '所持している'

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '6px', flexWrap: 'wrap' }}>
      <button
        className={`filter-btn ${owned ? 'active' : ''}`}
        type="button"
        aria-pressed={owned}
        disabled={checking || busy}
        onClick={toggleOwned}
      >
        {label}
      </button>
      {status && <span role="status" style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>{status}</span>}
    </div>
  )
}
