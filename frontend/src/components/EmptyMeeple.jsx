import React from 'react'

export const EmptyMeeple = ({ query }) => {
  return (
    <div className="mascot-state">
      <img
        src="/assets/header-icon.png"
        alt="Empty Meeple"
        style={{ width: '80px', height: 'auto', marginBottom: '16px', opacity: 0.7, filter: 'grayscale(50%)' }}
      />
      <p className="mascot-text">
        「{query}」は見つかりませんでした...
        <br />
        <span style={{ fontSize: '0.9em', color: 'var(--text-muted)' }}>
          右上の「生成」ボタンで新しく作れるかも？
        </span>
      </p>
    </div>
  )
}
