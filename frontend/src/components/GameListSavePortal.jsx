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
  const [host] = useState(() => {
    if (typeof document === 'undefined') return null
    const node = document.createElement('span')
    node.dataset.gameListSavePortal = 'true'
    node.style.display = 'contents'
    return node
  })
  const [portal, setPortal] = useState(null)

  useEffect(() => {
    let active = true
    let observer = null
    let game = null
    const pathname = location.pathname
    const slug = gameSlug(pathname)

    if (!slug || !host) return () => { active = false }

    const resolveTarget = () => {
      if (!active || !game) return
      const target = document.querySelector('.game-page-toolbar .header-actions')
      if (!target || !target.isConnected) return
      if (host.parentNode !== target) target.appendChild(host)
      setPortal((current) => {
        if (current?.pathname === pathname && current?.game?.id === game.id) return current
        return { pathname, game }
      })
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
      if (host.parentNode) host.remove()
    }
  }, [host, location.pathname])

  if (!host || !portal || portal.pathname !== location.pathname || !portal.game) return null
  return createPortal(
    <>
      <OwnedGameButton game={portal.game} />
      <AddToListButton game={portal.game} />
    </>,
    host,
  )
}
