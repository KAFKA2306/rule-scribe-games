import { useAuth } from '../auth/authContext'

export default function LoginButton() {
  const { user, loading, isConfigured, signInWithGoogle, signOut, error } = useAuth()

  if (loading) {
    return (
      <button className="button-secondary" type="button" disabled aria-label="認証状態を確認中">
        AUTH...
      </button>
    )
  }

  if (user) {
    const avatarUrl = user.user_metadata?.avatar_url
    const displayName = user.user_metadata?.full_name || user.email || 'USER'

    return (
      <div className="user-menu" data-auth-state="signed-in" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        {avatarUrl ? (
          <img
            src={avatarUrl}
            alt=""
            className="user-avatar"
            width="32"
            height="32"
            style={{ borderRadius: '50%' }}
          />
        ) : null}
        <span style={{ fontSize: '0.75rem', maxWidth: '160px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
          {displayName}
        </span>
        <button type="button" onClick={signOut} className="button-secondary" style={{ fontSize: '0.8rem', padding: '4px 8px' }}>
          ログアウト
        </button>
      </div>
    )
  }

  return (
    <div data-auth-state="signed-out" title={error || undefined}>
      <button
        type="button"
        onClick={signInWithGoogle}
        className="button-secondary"
        disabled={!isConfigured}
        aria-label="Googleでログイン"
      >
        Googleでログイン
      </button>
    </div>
  )
}
