import { useEffect, useRef, useState } from 'react'
import { Outlet, ScrollRestoration, useLocation, useNavigationType } from 'react-router-dom'

import AuthControlPortal from './AuthControlPortal.jsx'
import GameListSavePortal from './GameListSavePortal.jsx'

function isPlainPrimaryClick(event) {
  return event.button === 0 && !event.metaKey && !event.ctrlKey && !event.shiftKey && !event.altKey
}

export default function AppShell() {
  const location = useLocation()
  const navigationType = useNavigationType()
  const routeRef = useRef(null)
  const [navigating, setNavigating] = useState(false)

  useEffect(() => {
    const onClick = (event) => {
      if (!isPlainPrimaryClick(event)) return
      const anchor = event.target.closest?.('a[href]')
      if (!anchor || anchor.target === '_blank' || anchor.hasAttribute('download')) return
      const url = new URL(anchor.href, window.location.href)
      if (url.origin !== window.location.origin) return
      if (`${url.pathname}${url.search}${url.hash}` === `${window.location.pathname}${window.location.search}${window.location.hash}`) return
      setNavigating(true)
    }
    document.addEventListener('click', onClick, true)
    return () => document.removeEventListener('click', onClick, true)
  }, [])

  useEffect(() => {
    const timer = window.setTimeout(() => setNavigating(false), 150)
    if (navigationType !== 'POP') {
      window.requestAnimationFrame(() => {
        routeRef.current?.focus({ preventScroll: true })
        window.scrollTo({ top: 0, left: 0, behavior: 'auto' })
      })
    }
    return () => window.clearTimeout(timer)
  }, [location.key, navigationType])

  return (
    <>
      {navigating && (
        <div
          role="status"
          aria-live="polite"
          data-navigation-feedback
          style={{ position: 'fixed', top: 0, left: 0, right: 0, zIndex: 10000, height: '3px', background: 'var(--accent-primary, currentColor)' }}
        >
          <span className="sr-only">画面を切り替えています</span>
        </div>
      )}
      <div id="route-content" ref={routeRef} tabIndex={-1} style={{ outline: 'none' }}>
        <Outlet />
      </div>
      <AuthControlPortal />
      <GameListSavePortal />
      <ScrollRestoration />
    </>
  )
}
