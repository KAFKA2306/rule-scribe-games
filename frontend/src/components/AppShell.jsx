import { useEffect, useRef, useState } from 'react'
import { Outlet, useLocation, useNavigationType } from 'react-router-dom'

import AuthControlPortal from './AuthControlPortal.jsx'

function isPlainPrimaryClick(event) {
  return event.button === 0 && !event.metaKey && !event.ctrlKey && !event.shiftKey && !event.altKey
}

function focusRouteContent() {
  const target = document.querySelector('main, .game-detail-content')
  if (!target) return false
  if (!target.hasAttribute('tabindex')) target.setAttribute('tabindex', '-1')
  target.focus({ preventScroll: true })
  return true
}

export default function AppShell() {
  const location = useLocation()
  const navigationType = useNavigationType()
  const scrollPositions = useRef(new Map())
  const [navigating, setNavigating] = useState(false)

  useEffect(() => {
    const previous = window.history.scrollRestoration
    window.history.scrollRestoration = 'manual'
    return () => { window.history.scrollRestoration = previous }
  }, [])

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
    const key = location.key
    const positions = scrollPositions.current
    const feedbackTimer = window.setTimeout(() => setNavigating(false), 300)
    let focusObserver = null
    let focusTimer = null

    window.requestAnimationFrame(() => {
      if (navigationType === 'POP') {
        const saved = positions.get(key)
        if (saved) window.scrollTo({ top: saved.y, left: saved.x, behavior: 'auto' })
        return
      }

      window.scrollTo({ top: 0, left: 0, behavior: 'auto' })
      if (focusRouteContent()) return

      focusObserver = new MutationObserver(() => {
        if (!focusRouteContent()) return
        focusObserver?.disconnect()
        focusObserver = null
        if (focusTimer) window.clearTimeout(focusTimer)
      })
      focusObserver.observe(document.getElementById('root') || document.body, { childList: true, subtree: true })
      focusTimer = window.setTimeout(() => {
        focusObserver?.disconnect()
        focusObserver = null
      }, 1000)
    })

    return () => {
      window.clearTimeout(feedbackTimer)
      if (focusTimer) window.clearTimeout(focusTimer)
      focusObserver?.disconnect()
      positions.set(key, { x: window.scrollX, y: window.scrollY })
    }
  }, [location.key, navigationType])

  return (
    <>
      {navigating && (
        <div
          role="status"
          aria-live="polite"
          data-navigation-feedback
          style={{ position: 'fixed', top: 0, left: 0, right: 0, zIndex: 10000, height: '3px', overflow: 'hidden', background: 'var(--accent-primary, currentColor)' }}
        >
          <span style={{ position: 'absolute', width: '1px', height: '1px', overflow: 'hidden', clip: 'rect(0 0 0 0)', whiteSpace: 'nowrap' }}>
            画面を切り替えています
          </span>
        </div>
      )}
      <Outlet />
      <AuthControlPortal />
    </>
  )
}
