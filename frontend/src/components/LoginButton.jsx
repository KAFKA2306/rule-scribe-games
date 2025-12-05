import { supabase } from '../lib/supabase'

export default function LoginButton({ session }) {
  const handleLogout = async () => {
    const { error } = await supabase.auth.signOut()
    if (error) console.log('Error logging out:', error.message)
  }

  if (session) {
    return (
      <div className="user-menu">
        <img
          src={session.user.user_metadata.avatar_url}
          alt="Avatar"
          className="user-avatar"
          style={{
            width: '32px',
            height: '32px',
            borderRadius: '50%',
            marginRight: '8px',
            verticalAlign: 'middle',
          }}
        />
        <button
          onClick={handleLogout}
          className="button-secondary"
          style={{ fontSize: '0.8rem', padding: '4px 8px' }}
        >
          ログアウト
        </button>
      </div>
    )
  }

  return null
}
