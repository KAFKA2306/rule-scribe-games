import React from 'react'
import '../index.css'

export const ThinkingMeeple = ({
  text = 'ルールブックを読んでいます...',
  imageSrc = '/assets/thinking-meeple.png',
}) => {
  return (
    <div className="mascot-state">
      <div className="mascot-image-container">
        <img
          src={imageSrc}
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
