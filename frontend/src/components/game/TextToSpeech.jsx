import { useState, useEffect } from 'react'

export const TextToSpeech = ({ text }) => {
  const [speaking, setSpeaking] = useState(false)
  const [supported] = useState(() => typeof window !== 'undefined' && 'speechSynthesis' in window)

  useEffect(() => {
    return () => {
      if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
        window.speechSynthesis.cancel()
      }
    }
  }, [])

  const handleSpeak = () => {
    if (!supported) return

    if (speaking) {
      window.speechSynthesis.cancel()
      setSpeaking(false)
      return
    }

    const utterance = new SpeechSynthesisUtterance(text)
    utterance.lang = 'ja-JP'
    utterance.rate = 0.9
    utterance.pitch = 1.0
    utterance.onend = () => setSpeaking(false)
    utterance.onerror = () => setSpeaking(false)

    window.speechSynthesis.speak(utterance)
    setSpeaking(true)
  }

  if (!supported) return null

  return (
    <button
      onClick={handleSpeak}
      className={`share-btn ${speaking ? 'speaking' : ''}`}
      title={speaking ? '読み上げ停止' : '読み上げ開始'}
      aria-label="Text to speech"
      aria-pressed={speaking}
    >
      {speaking ? '⏹️ 停止' : '🔊 読上'}
    </button>
  )
}
