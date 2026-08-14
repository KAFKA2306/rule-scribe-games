import { useEffect, useState } from 'react'
import { createPortal } from 'react-dom'

import { useAuth } from '../auth/authContext'
import LoginButton from './LoginButton'

function findTarget() {
  return document.querySelector('header') || document.querySelector('.game-page-toolbar')
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
    <div data-auth-control style={{ marginLeft: 'auto', display: 'flex', gap: '8px', alignItems: 'center', flexWrap: 'wrap' }}>
      {user && <a href="/lists" className="filter-btn" style={{ textDecoration: 'none' }}>マイリスト</a>}
      <LoginButton />
    </div>,
    target,
  )
}
