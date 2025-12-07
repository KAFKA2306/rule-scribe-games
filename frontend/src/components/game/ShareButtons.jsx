import { useState } from 'react'

export const ShareButton = ({ slug }) => {
  const [copied, setCopied] = useState(false)

  const handleShare = async () => {
    const url = `https://bodoge-no-mikata.vercel.app/games/${slug}`
    if (navigator.clipboard && navigator.clipboard.writeText) {
      await navigator.clipboard.writeText(url)
    }
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <button
      onClick={handleShare}
      className={`share-btn ${copied ? 'copied' : ''}`}
      title={copied ? 'コピーしました' : 'リンクをコピー'}
      aria-label="Share this game"
    >
      {copied ? '✓ 完了' : '🔗 コピー'}
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
