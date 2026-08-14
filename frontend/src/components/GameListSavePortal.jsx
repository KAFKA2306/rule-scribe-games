import { useEffect, useState } from 'react'
import { createPortal } from 'react-dom'

import { api } from '../lib/api'
import AddToListButton from './game/AddToListButton'

function currentGameSlug() {
  const match = window.location.pathname.match(/^\/games\/([^/]+)\/?$/)
  return match ? decodeURIComponent(match[1]) : null
}

export default function GameListSavePortal() {
  const [target, setTarget] = useState(null)
  const [game, setGame] = useState(null)

  useEffect(() => {
    let active = true
    const resolve = async () => {
      const slug = currentGameSlug()
      const nextTarget = document.querySelector('.game-page-toolbar .header-actions')
      setTarget(nextTarget)
      if (!slug || !nextTarget) {
        setGame(null)
        return
      }
      try {
        const data = await api.get(`/api/games/${slug}`)
        if (!active) return
        setGame(Array.isArray(data) ? data[0] : data.game || data)
      } catch {
        if (active) setGame(null)
      }
    }

    resolve()
    const root = document.getElementById('root')
    if (!root) return () => { active = false }
    const observer = new MutationObserver(resolve)
    observer.observe(root, { childList: true, subtree: true })
    return () => {
      active = false
      observer.disconnect()
    }
  }, [])

  if (!target || !game) return null
  return createPortal(<AddToListButton game={game} />, target)
}
