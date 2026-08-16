import { useState } from 'react'

export const ShareButton = ({ slug }) => {
  const [status, setStatus] = useState('idle')

  const handleShare = async () => {
    const url = `https://bodoge-no-mikata.vercel.app/games/${slug}`

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

  const label = status === 'copied'
    ? 'コピーしました'
    : status === 'error'
      ? 'コピーできませんでした'
      : 'リンクをコピー'

  return (
    <button
      onClick={handleShare}
      className={`share-btn ${status === 'copied' ? 'copied' : ''}`}
      title={label}
      aria-label={label}
    >
      {status === 'copied' ? '✓ 完了' : status === 'error' ? 'コピー失敗' : '🔗 コピー'}
    </button>
  )
}

export const TwitterShareButton = ({ slug, title }) => {
  const handleTwitterShare = () => {
    const text = `ボードゲーム「${title}」が気になる！ルールや魅力を3分でチェック！`
    const url = `https://bodoge-no-mikata.vercel.app/games/${slug}`
    const hashtags = 'ボドゲのミカタ,ボードゲーム'
    const twitterUrl = `https://twitter.com/intent/tweet?text=${encodeURIComponent(text)}&url=${encodeURIComponent(url)}&hashtags=${hashtags}`
    window.open(twitterUrl, '_blank', 'noopener,noreferrer')
  }

  return (
    <button
      onClick={handleTwitterShare}
      className="share-btn twitter"
      title="X(Twitter)でシェア"
      aria-label="Share on X"
    >
      𝕏 共有
    </button>
  )
}
