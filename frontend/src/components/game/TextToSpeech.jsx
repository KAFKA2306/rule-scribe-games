import { useState, useEffect } from 'react'

export const TextToSpeech = ({ text }) => {
  const [speechState, setSpeechState] = useState('idle')
  const [supported] = useState(() => typeof window !== 'undefined' && 'speechSynthesis' in window)
  const active = speechState !== 'idle'

  useEffect(() => {
    return () => {
      if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
        window.speechSynthesis.cancel()
      }
    }
  }, [])

  const handleSpeak = () => {
    if (!supported) return

    if (active) {
      window.speechSynthesis.cancel()
      setSpeechState('idle')
      return
    }

    const utterance = new SpeechSynthesisUtterance(text)
    utterance.lang = 'ja-JP'
    utterance.rate = 0.9
    utterance.pitch = 1.0
    utterance.onstart = () => setSpeechState('speaking')
    utterance.onend = () => setSpeechState('idle')
    utterance.onerror = () => setSpeechState('idle')

    window.speechSynthesis.speak(utterance)
    setSpeechState('queued')
  }

  if (!supported) return null

  return (
    <button
      onClick={handleSpeak}
      className={`share-btn ${speechState === 'speaking' ? 'speaking' : ''}`}
      title={active ? '要点の読み上げを停止' : 'ページの要点を読み上げ'}
      aria-label={active ? '要点の読み上げを停止' : 'ページの要点を読み上げ'}
      aria-pressed={active}
    >
      {active ? '⏹️ 停止' : '🔊 要点'}
    </button>
  )
}
