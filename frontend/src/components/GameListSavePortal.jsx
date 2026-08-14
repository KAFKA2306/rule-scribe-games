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
    let resolved = false
    let requestInFlight = false
    const pathname = location.pathname
    const slug = gameSlug(pathname)

    if (!slug) return () => { active = false }

    const mount = async () => {
      if (!active || resolved || requestInFlight) return
      const target = document.querySelector('.game-page-toolbar .header-actions')
      if (!target) return

      requestInFlight = true
      try {
        const data = await api.get(`/api/games/${slug}`)
        if (!active) return
        if (!target.isConnected) {
          requestInFlight = false
          void mount()
          return
        }
        const game = Array.isArray(data) ? data[0] : data.game || data
        resolved = true
        observer?.disconnect()
        observer = null
        setPortal({ pathname, target, game })
      } catch {
        requestInFlight = false
      }
    }

    mount()
    const root = document.getElementById('root')
    if (root) {
      observer = new MutationObserver(mount)
      observer.observe(root, { childList: true, subtree: true })
    }

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
