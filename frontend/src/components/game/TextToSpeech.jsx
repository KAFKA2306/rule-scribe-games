import { useState, useEffect } from 'react'

function visibleText(selector) {
  const element = document.querySelector(selector)
  return element?.textContent?.trim() || ''
}

function buildVisibleNarration(fallbackText) {
  if (typeof document === 'undefined') return fallbackText

  const title = visibleText('.game-title')
  const coachSteps = [...document.querySelectorAll('.coach-mode .coach-step')]
    .map((element) => element.textContent?.trim())
    .filter(Boolean)
  const synopsis = visibleText('.pro-card--synopsis .summary-text')
  const trustState = [...document.querySelectorAll('[aria-label="出典・根拠"] .game-empty-note')]
    .map((element) => element.textContent?.trim())
    .filter(Boolean)

  const content = coachSteps.length > 0
    ? coachSteps
    : synopsis
      ? [synopsis]
      : []

  const sections = [title, ...content, ...trustState].filter(Boolean)
  return sections.length > 0 ? sections.join('。 ') : fallbackText
}

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

    const utterance = new SpeechSynthesisUtterance(buildVisibleNarration(text))
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
