import { useEffect, useState } from 'react'
import { createPortal } from 'react-dom'
import { useLocation } from 'react-router-dom'

import { api } from '../lib/api'
import AddToListButton from './game/AddToListButton'
import OwnedGameButton from './game/OwnedGameButton'

function gameSlug(pathname) {
  const match = pathname.match(/^\/games\/([^/]+)\/?$/)
  return match ? decodeURIComponent(match[1]) : null
}

export default function GameListSavePortal() {
  const location = useLocation()
  const [target, setTarget] = useState(null)
  const [game, setGame] = useState(null)

  useEffect(() => {
    let active = true
    let observer = null
    let resolved = false
    const slug = gameSlug(location.pathname)

    setTarget(null)
    setGame(null)
    if (!slug) return () => { active = false }

    const mount = async () => {
      if (!active || resolved) return
      const nextTarget = document.querySelector('.game-page-toolbar .header-actions')
      if (!nextTarget) return

      resolved = true
      observer?.disconnect()
      observer = null
      setTarget(nextTarget)

      try {
        const data = await api.get(`/api/games/${slug}`)
        if (!active) return
        setGame(Array.isArray(data) ? data[0] : data.game || data)
      } catch {
        if (active) setGame(null)
      }
    }

    mount()
    if (!resolved) {
      const root = document.getElementById('root')
      if (root) {
        observer = new MutationObserver(mount)
        observer.observe(root, { childList: true, subtree: true })
      }
    }

    return () => {
      active = false
      observer?.disconnect()
    }
  }, [location.pathname])

  if (!target || !game) return null
  return createPortal(
    <>
      <OwnedGameButton game={game} />
      <AddToListButton game={game} />
    </>,
    target,
  )
}
