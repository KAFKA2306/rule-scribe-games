import { useEffect, useState } from 'react'
import { createPortal } from 'react-dom'
import { Link, useLocation } from 'react-router-dom'

import { useAuth } from '../auth/authContext'
import LoginButton from './LoginButton'

function findTarget(pathname) {
  if (pathname === '/lists') return null
  const explicitTarget = document.querySelector('[data-auth-control-target]')
  if (explicitTarget) return explicitTarget
  return document.querySelector('header') || document.querySelector('.game-page-toolbar')
}

export default function AuthControlPortal() {
  const location = useLocation()
  const [target, setTarget] = useState(null)
  const { user } = useAuth()

  useEffect(() => {
    const resolveTarget = () => setTarget(findTarget(location.pathname))
    resolveTarget()

    const root = document.getElementById('root')
    if (!root) return undefined

    const observer = new MutationObserver(resolveTarget)
    observer.observe(root, { childList: true, subtree: true })
    return () => observer.disconnect()
  }, [location.pathname])

  if (!target) return null

  return createPortal(
    <div data-auth-control className="auth-control-cluster">
      {user && <Link to="/lists" className="filter-btn auth-control-cluster__lists">マイリスト</Link>}
      <LoginButton />
    </div>,
    target,
  )
}
