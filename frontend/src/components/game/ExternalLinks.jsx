const isValidUrl = (url) => {
  if (!url || typeof url !== 'string') return false
  const trimmed = url.trim()
  if (!trimmed) return false

  try {
    const parsed = new URL(trimmed)
    return parsed.protocol === 'http:' || parsed.protocol === 'https:'
  } catch {
    return false
  }
}

const identityLabels = {
  verified: '確認済み',
  unverified: '未検証',
}

const sourceTrustLabels = {
  publisher_primary: '出版社一次資料',
  platform_primary: 'プラットフォーム一次資料',
  secondary: '二次資料',
  tertiary: '三次資料',
  unknown: '未確認',
}

const contentReviewLabels = {
  publisher_reviewed: '出版社確認済み',
  human_reviewed: '人手確認済み',
  ai_draft: 'AI下書き / 未確認',
}

export const ExternalLinks = ({ game }) => {
  const { affiliate_urls, official_url, bgg_url, amazon_url } = game
  const amazon = affiliate_urls?.amazon || amazon_url
  const rakuten = affiliate_urls?.rakuten
  const yahoo = affiliate_urls?.yahoo

  const links = [
    { url: amazon, label: 'Amazon', class: 'amazon' },
    { url: rakuten, label: '楽天で見る', class: 'rakuten' },
    { url: yahoo, label: 'Yahoo!で見る', class: 'yahoo' },
    { url: official_url, label: '出版社・製品公式', class: 'official' },
    { url: bgg_url, label: 'BoardGameGeek', class: 'bgg' },
    { url: game.bga_url, label: 'Board Game Arena', class: 'bga' },
  ].filter((link) => isValidUrl(link.url))

  const identity = identityLabels[game.identity_status] || '未検証'
  const sourceTrust = sourceTrustLabels[game.source_trust_status] || '未確認'
  const contentReview = contentReviewLabels[game.content_review_status] || 'AI下書き / 未確認'

  return (
    <div className="info-section">
      <div aria-label="情報の信頼状態" style={{ display: 'grid', gap: '8px', marginBottom: links.length ? '14px' : 0 }}>
        <div><strong>ゲーム同定:</strong> {identity}</div>
        <div><strong>ルール出典:</strong> {sourceTrust}</div>
        <div><strong>内容レビュー:</strong> {contentReview}</div>
        <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', lineHeight: 1.5 }}>
          3項目は独立した判定です。URLの存在や旧 is_official 値だけで「公式確認済み」にはしません。
        </div>
      </div>

      {links.length > 0 && (
        <>
          <h3>Links</h3>
          <div className="external-links-grid">
            {links.map((link) => (
              <a
                key={`${link.class}:${link.url}`}
                href={link.url}
                target="_blank"
                rel="noopener noreferrer sponsored"
                className={`link-button ${link.class}`}
              >
                {link.label}
              </a>
            ))}
          </div>
        </>
      )}
    </div>
  )
}
