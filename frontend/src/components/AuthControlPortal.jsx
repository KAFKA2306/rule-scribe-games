import { useEffect, useState } from 'react'
import { createPortal } from 'react-dom'
import { Link } from 'react-router-dom'

import { useAuth } from '../auth/authContext'
import LoginButton from './LoginButton'

function findTarget() {
  return document.querySelector('[data-auth-control-target]') || document.querySelector('header') || document.querySelector('.game-page-toolbar')
}

export default function AuthControlPortal() {
  const [target, setTarget] = useState(null)
  const { user } = useAuth()

  useEffect(() => {
    const resolveTarget = () => setTarget(findTarget())
    resolveTarget()

    const root = document.getElementById('root')
    if (!root) return undefined

    const observer = new MutationObserver(resolveTarget)
    observer.observe(root, { childList: true, subtree: true })
    return () => observer.disconnect()
  }, [])

  if (!target) return null

  return createPortal(
    <div data-auth-control className="auth-control-cluster">
      {user && <Link to="/lists" className="filter-btn auth-control-cluster__lists">マイリスト</Link>}
      <LoginButton />
    </div>,
    target,
  )
}
