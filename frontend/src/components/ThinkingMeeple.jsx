import React from 'react'
import '../index.css'

export const ThinkingMeeple = ({ text = 'ルールブックを読んでいます...' }) => {
  return (
    <div className="mascot-state">
      <div className="mascot-image-container">
        <img
          src="/assets/thinking-meeple.png"
          alt="Thinking Meeple"
          className="mascot-bounce"
          style={{ width: '80px', height: 'auto', marginBottom: '16px' }}
        />
      </div>
      <p className="mascot-text">{text}</p>
      <div className="spinner-dots">
        <span>.</span>
        <span>.</span>
        <span>.</span>
      </div>
    </div>
  )
}
