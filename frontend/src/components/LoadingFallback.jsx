export default function LoadingFallback() {
  return (
    <div
      style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        minHeight: '100vh',
        background: 'var(--bg-primary, #0b1221)',
      }}
    >
      <p style={{ color: 'var(--text-primary, #fff)' }}>読み込み中...</p>
    </div>
  )
}
