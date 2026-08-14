import { useEffect, useRef, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'

import { useAuth } from '../auth/authContext'
import { api } from '../lib/api'
import './ListsPage.css'

const OWNED_SELECTION = '__owned__'

export default function ListsPage() {
  const { user, loading: authLoading, signInWithGoogle } = useAuth()
  const [searchParams, setSearchParams] = useSearchParams()
  const selectedId = searchParams.get('list') || OWNED_SELECTION
  const savedNotice = searchParams.get('notice') === 'saved'
  const [lists, setLists] = useState([])
  const [indexReady, setIndexReady] = useState(false)
  const [detail, setDetail] = useState(null)
  const detailCache = useRef(new Map())
  const [newName, setNewName] = useState('')
  const [loading, setLoading] = useState(false)
  const [busyAction, setBusyAction] = useState('')
  const [error, setError] = useState('')

  const loadDetail = async (id) => (
    id === OWNED_SELECTION
      ? api.get('/api/owned-games')
      : api.get(`/api/lists/${id}`)
  )

  const chooseList = (id, { replace = false, notice = '' } = {}) => {
    const next = new URLSearchParams(searchParams)
    if (id === OWNED_SELECTION) next.delete('list')
    else next.set('list', id)
    if (notice) next.set('notice', notice)
    else next.delete('notice')
    setSearchParams(next, { replace })
  }

  const fetchSelectedDetail = async (id, { force = false } = {}) => {
    if (!force && detailCache.current.has(id)) {
      setDetail(detailCache.current.get(id))
      return detailCache.current.get(id)
    }
    setLoading(true)
    setError('')
    try {
      const nextDetail = await loadDetail(id)
      detailCache.current.set(id, nextDetail)
      setDetail(nextDetail)
      return nextDetail
    } catch (err) {
      setError(err.message)
      throw err
    } finally {
      setLoading(false)
    }
  }

  const refreshIndex = async () => {
    const data = await api.get('/api/lists')
    const next = data.lists || []
    setLists(next)
    return next
  }

  const bootstrap = async (id) => {
    setLoading(true)
    setError('')
    try {
      const detailPromise = loadDetail(id)
      const indexPromise = api.get('/api/lists')
      const [data, nextDetail] = await Promise.all([indexPromise, detailPromise])
      const nextLists = data.lists || []
      setLists(nextLists)
      setIndexReady(true)
      detailCache.current.set(id, nextDetail)
      setDetail(nextDetail)

      if (id !== OWNED_SELECTION && !nextLists.some((list) => list.id === id)) {
        detailCache.current.delete(id)
        chooseList(OWNED_SELECTION, { replace: true })
      }
    } catch (err) {
      setIndexReady(false)
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    detailCache.current.clear()
    setIndexReady(false)
    if (user) bootstrap(selectedId)
    else {
      setLists([])
      setDetail(null)
    }
    // User changes reset the private cache; initial list index/detail load is parallel.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user])

  useEffect(() => {
    if (!user || !indexReady) return
    const valid = selectedId === OWNED_SELECTION || lists.some((list) => list.id === selectedId)
    if (!valid) {
      chooseList(OWNED_SELECTION, { replace: true })
      return
    }
    fetchSelectedDetail(selectedId).catch(() => {})
    // Browser back/forward changes only the detail request; the list index is retained.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedId, indexReady])

  const retryLoad = () => {
    api.clearGetCache()
    if (!indexReady) bootstrap(selectedId)
    else fetchSelectedDetail(selectedId, { force: true }).catch(() => {})
  }

  const createList = async (event) => {
    event.preventDefault()
    const name = newName.trim()
    if (!name || busyAction) return
    setBusyAction('create')
    setError('')
    try {
      const created = await api.post('/api/lists', { name, visibility: 'private' })
      setNewName('')
      const nextLists = await refreshIndex()
      setIndexReady(true)
      if (nextLists.some((list) => list.id === created.id)) chooseList(created.id)
    } catch (err) {
      setError(err.message)
    } finally {
      setBusyAction('')
    }
  }

  const renameList = async () => {
    if (!detail || detail.system_key || busyAction) return
    const name = window.prompt('新しいリスト名', detail.name)?.trim()
    if (!name || name === detail.name) return
    setBusyAction('rename')
    setError('')
    try {
      const renamed = await api.patch(`/api/lists/${detail.id}`, { name })
      const nextDetail = { ...detail, ...renamed, items: detail.items }
      detailCache.current.set(selectedId, nextDetail)
      setDetail(nextDetail)
      await refreshIndex()
    } catch (err) {
      setError(err.message)
    } finally {
      setBusyAction('')
    }
  }

  const deleteList = async () => {
    if (!detail || detail.system_key || busyAction || !window.confirm(`「${detail.name}」を削除しますか？`)) return
    setBusyAction('delete')
    setError('')
    try {
      await api.delete(`/api/lists/${detail.id}`)
      detailCache.current.delete(selectedId)
      await refreshIndex()
      chooseList(OWNED_SELECTION)
    } catch (err) {
      setError(err.message)
    } finally {
      setBusyAction('')
    }
  }

  const removeItem = async (item) => {
    if (!detail || busyAction) return
    setBusyAction(`remove:${item.id}`)
    setError('')
    try {
      if (detail.system_key === 'owned' && item.game_id) {
        await api.delete(`/api/owned-games/${item.game_id}`)
      } else if (detail.id) {
        await api.delete(`/api/lists/${detail.id}/items/${item.id}`)
      }
      const nextDetail = { ...detail, items: detail.items.filter((candidate) => candidate.id !== item.id) }
      detailCache.current.set(selectedId, nextDetail)
      setDetail(nextDetail)
    } catch (err) {
      setError(err.message)
    } finally {
      setBusyAction('')
    }
  }

  const moveItem = async (index, delta) => {
    if (!detail?.id || busyAction) return
    const nextIndex = index + delta
    if (nextIndex < 0 || nextIndex >= detail.items.length) return
    const previous = detail
    const items = [...detail.items]
    ;[items[index], items[nextIndex]] = [items[nextIndex], items[index]]
    const optimistic = { ...detail, items }
    detailCache.current.set(selectedId, optimistic)
    setDetail(optimistic)
    setBusyAction('reorder')
    setError('')
    try {
      await api.put(`/api/lists/${detail.id}/order`, { item_ids: items.map((item) => item.id) })
    } catch (err) {
      detailCache.current.set(selectedId, previous)
      setDetail(previous)
      setError(err.message)
    } finally {
      setBusyAction('')
    }
  }

  if (authLoading) {
    return (
      <main className="lists-page" aria-busy="true">
        <div className="lists-loading-shell">
          <div className="lists-loading-shell__label">認証状態を確認しています…</div>
          <div className="pro-card lists-loading-shell__card">マイリストを準備しています。</div>
        </div>
      </main>
    )
  }

  if (!user) {
    return (
      <main className="lists-page">
        <div className="lists-shell">
          <header className="lists-header">
            <div className="lists-header__identity">
              <Link to="/" className="back-link">← DIRECTORY</Link>
              <h1>マイリスト</h1>
            </div>
          </header>
          <div className="pro-card lists-empty">
            <div>
              <p>所持ゲームやリストの保存にはログインが必要です。</p>
              <button type="button" className="filter-btn active" onClick={signInWithGoogle}>Googleでログイン</button>
            </div>
          </div>
        </div>
      </main>
    )
  }

  return (
    <main className="lists-page" aria-busy={loading || Boolean(busyAction)}>
      <div className="lists-shell">
        <header className="lists-header" data-auth-control-target>
          <div className="lists-header__identity">
            <Link to="/" className="back-link">← DIRECTORY</Link>
            <h1>マイリスト</h1>
          </div>
        </header>

        <form className="lists-create" onSubmit={createList}>
          <input
            className="search-input"
            value={newName}
            maxLength={80}
            disabled={Boolean(busyAction)}
            onChange={(event) => setNewName(event.target.value)}
            placeholder="新しいリスト名"
            aria-label="新しいリスト名"
          />
          <button className="filter-btn" type="submit" disabled={Boolean(busyAction)}>
            {busyAction === 'create' ? '作成中…' : 'リストを作成'}
          </button>
        </form>

        {savedNotice && <div role="status" className="lists-feedback">保存したリストを表示しています。</div>}
        {error && (
          <div role="alert" className="lists-feedback lists-feedback--error">
            <span>{error}</span>
            <button type="button" className="filter-btn" onClick={retryLoad} disabled={loading || Boolean(busyAction)}>再試行</button>
          </div>
        )}
        {loading && <div role="status" className="lists-feedback">読み込み中…</div>}
        {busyAction && <div role="status" className="lists-feedback">変更を反映しています…</div>}

        <div className="lists-workspace">
          <aside className="lists-nav" aria-label="マイリスト一覧">
            <button
              type="button"
              className={`filter-btn lists-nav__button ${selectedId === OWNED_SELECTION ? 'active' : ''}`}
              disabled={loading}
              onClick={() => chooseList(OWNED_SELECTION)}
            >
              所持ゲーム
            </button>
            {lists.map((list) => (
              <button
                type="button"
                key={list.id}
                className={`filter-btn lists-nav__button ${selectedId === list.id ? 'active' : ''}`}
                disabled={loading}
                onClick={() => chooseList(list.id)}
              >
                {list.name}
              </button>
            ))}
            {lists.length === 0 && !loading && <div className="lists-nav__empty">custom listはまだありません。</div>}
          </aside>

          <section className="lists-detail" aria-live="polite">
            {detail && (
              <>
                <div className="lists-detail__header">
                  <h2>{detail.name}</h2>
                  {!detail.system_key && (
                    <div className="lists-detail__actions">
                      <button type="button" className="filter-btn" disabled={Boolean(busyAction)} onClick={renameList}>
                        {busyAction === 'rename' ? '変更中…' : '名前変更'}
                      </button>
                      <button type="button" className="filter-btn lists-danger" disabled={Boolean(busyAction)} onClick={deleteList}>
                        {busyAction === 'delete' ? '削除中…' : 'リストを削除'}
                      </button>
                    </div>
                  )}
                </div>

                {detail.items.length === 0 ? (
                  <div className="pro-card lists-empty">
                    {detail.system_key === 'owned'
                      ? '所持ゲームはまだありません。ゲーム詳細から「所持している」を選択してください。'
                      : 'このリストは空です。ゲーム詳細から追加できます。'}
                  </div>
                ) : (
                  <div className="lists-items">
                    {detail.items.map((item, index) => {
                      const title = item.game?.title_ja || item.game?.title || item.game_title_snapshot
                      const removing = busyAction === `remove:${item.id}`
                      return (
                        <article key={item.id} className="pro-card lists-item" data-removing={removing ? 'true' : 'false'}>
                          <div className="lists-item__content">
                            {item.game ? (
                              <Link className="lists-item__title" to={`/games/${item.game.slug}`}>{title}</Link>
                            ) : (
                              <strong className="lists-item__title">{title}</strong>
                            )}
                            {item.unavailable && <div className="lists-item__meta lists-item__meta--unavailable">現在利用できないゲーム</div>}
                            {detail.system_key === 'owned' && item.created_at && (
                              <div className="lists-item__meta">登録: {new Date(item.created_at).toLocaleDateString('ja-JP')}</div>
                            )}
                          </div>
                          <div className="lists-item__actions">
                            <div className="lists-item__reorder" aria-label={`${title}の並べ替え`}>
                              <button type="button" className="filter-btn" aria-label={`${title}を上へ`} disabled={Boolean(busyAction) || index === 0} onClick={() => moveItem(index, -1)}>↑</button>
                              <button type="button" className="filter-btn" aria-label={`${title}を下へ`} disabled={Boolean(busyAction) || index === detail.items.length - 1} onClick={() => moveItem(index, 1)}>↓</button>
                            </div>
                            <button type="button" className="filter-btn lists-danger" disabled={Boolean(busyAction)} onClick={() => removeItem(item)}>
                              {removing ? '反映中…' : detail.system_key === 'owned' ? '所持解除' : 'リストから削除'}
                            </button>
                          </div>
                        </article>
                      )
                    })}
                  </div>
                )}
              </>
            )}
          </section>
        </div>
      </div>
    </main>
  )
}
