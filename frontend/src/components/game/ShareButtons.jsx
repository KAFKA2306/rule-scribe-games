import { useState } from 'react'

export const ShareButton = ({ slug }) => {
  const [status, setStatus] = useState('idle')
  const canNativeShare = typeof navigator !== 'undefined' && typeof navigator.share === 'function'

  const copyUrl = async (url) => {
    if (!navigator.clipboard?.writeText) {
      setStatus('error')
      return
    }

    try {
      await navigator.clipboard.writeText(url)
      setStatus('copied')
      setTimeout(() => setStatus('idle'), 2000)
    } catch (error) {
      console.error('Failed to copy game URL:', error)
      setStatus('error')
    }
  }

  const handleShare = async () => {
    const url = `https://bodoge-no-mikata.vercel.app/games/${slug}`
    const title = typeof document !== 'undefined' ? document.title : ''

    if (canNativeShare) {
      try {
        await navigator.share({ title, url })
        setStatus('shared')
        setTimeout(() => setStatus('idle'), 2000)
        return
      } catch (error) {
        if (error?.name === 'AbortError') {
          setStatus('idle')
          return
        }
      }
    }

    await copyUrl(url)
  }

  const label = status === 'shared'
    ? '共有しました'
    : status === 'copied'
      ? 'コピーしました'
      : status === 'error'
        ? '共有できませんでした'
        : canNativeShare
          ? '共有'
          : 'リンクをコピー'

  return (
    <button
      onClick={handleShare}
      className={`share-btn ${status === 'shared' || status === 'copied' ? 'copied' : ''}`}
      title={label}
      aria-label={label}
    >
      {status === 'shared' ? '✓ 共有' : status === 'copied' ? '✓ 完了' : status === 'error' ? '共有失敗' : canNativeShare ? '共有' : '🔗 コピー'}
    </button>
  )
}

export const TwitterShareButton = ({ slug, title }) => {
  const handleTwitterShare = () => {
    const text = `ボードゲーム「${title}」のルールを見る`
    const url = `https://bodoge-no-mikata.vercel.app/games/${slug}`
    const hashtags = 'ボドゲのミカタ,ボードゲーム'
    const twitterUrl = `https://twitter.com/intent/tweet?text=${encodeURIComponent(text)}&url=${encodeURIComponent(url)}&hashtags=${hashtags}`
    window.open(twitterUrl, '_blank', 'noopener,noreferrer')
  }

  return (
    <button
      onClick={handleTwitterShare}
      className="share-btn twitter"
      title="Xで共有"
      aria-label="Xで共有"
    >
      𝕏 共有
    </button>
  )
}
