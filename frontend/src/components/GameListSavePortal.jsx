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
  const [portal, setPortal] = useState(null)

  useEffect(() => {
    let active = true
    let observer = null
    let currentTarget = null
    let game = null
    const pathname = location.pathname
    const slug = gameSlug(pathname)

    if (!slug) return () => { active = false }

    const resolveTarget = () => {
      if (!active || !game) return
      const target = document.querySelector('.game-page-toolbar .header-actions')
      if (!target || !target.isConnected || target === currentTarget) return
      currentTarget = target
      setPortal({ pathname, target, game })
    }

    const root = document.getElementById('root')
    if (root) {
      observer = new MutationObserver(resolveTarget)
      observer.observe(root, { childList: true, subtree: true })
    }

    api.get(`/api/games/${slug}`)
      .then((data) => {
        if (!active) return
        game = Array.isArray(data) ? data[0] : data.game || data
        resolveTarget()
      })
      .catch(() => {})

    return () => {
      active = false
      observer?.disconnect()
    }
  }, [location.pathname])

  if (!portal || portal.pathname !== location.pathname || !portal.target.isConnected || !portal.game) return null
  return createPortal(
    <>
      <OwnedGameButton game={portal.game} />
      <AddToListButton game={portal.game} />
    </>,
    portal.target,
  )
}
