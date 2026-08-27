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

const hasAmazonAffiliateTag = (url) => {
  if (!isValidUrl(url)) return false

  try {
    const parsed = new URL(url)
    return parsed.hostname.toLowerCase().includes('amazon.') && Boolean(parsed.searchParams.get('tag'))
  } catch {
    return false
  }
}

const sourceLabel = (sourceTrust) => {
  if (sourceTrust === 'official_publisher') return '出版社のページ'
  if (sourceTrust === 'authorized_partner') return '認定パートナーのページ'
  if (sourceTrust === 'third_party') return '第三者の出典'
  return '登録済み出典（未検証）'
}

const trackAffiliateOutbound = (gameSlug, provider) => {
  if (typeof window === 'undefined' || typeof window.va !== 'function') return

  window.va('event', {
    name: 'Affiliate Outbound',
    data: {
      gameSlug,
      provider,
    },
  })
}

export const ExternalLinks = ({ game }) => {
  const { affiliate_urls, source_url, source_trust, bgg_url, amazon_url } = game
  const affiliateAmazon = affiliate_urls?.amazon
  const amazon = affiliateAmazon || amazon_url
  const rakuten = affiliate_urls?.rakuten
  const yahoo = affiliate_urls?.yahoo
  const source = isValidUrl(source_url)
    ? { url: source_url, label: sourceLabel(source_trust), class: 'source', sponsored: false }
    : null
  const links = [
    {
      url: amazon,
      label: 'Amazon',
      class: 'amazon',
      sponsored: Boolean(affiliateAmazon) || hasAmazonAffiliateTag(amazon_url),
    },
    { url: rakuten, label: '楽天で見る', class: 'rakuten', sponsored: true },
    { url: yahoo, label: 'Yahoo!で見る', class: 'yahoo', sponsored: true },
    { url: bgg_url, label: 'BoardGameGeek', class: 'bgg', sponsored: false },
    { url: game.bga_url, label: 'Board Game Arena', class: 'bga', sponsored: false },
  ].filter((link) => isValidUrl(link.url))

  if (!source && links.length === 0) return null

  return (
    <div className="info-section">
      {source && (
        <div aria-label="登録済み出典">
          <div className="game-empty-note">登録済み出典</div>
          <div className="external-links-grid">
            <a
              href={source.url}
              target="_blank"
              rel="noopener noreferrer"
              className="link-button source"
            >
              {source.label}
            </a>
          </div>
        </div>
      )}

      {links.length > 0 && (
        <div aria-label="その他のリンク">
          <div className="game-empty-note">その他のリンク</div>
          <div className="external-links-grid">
            {links.map((link) => (
              <a
                key={`${link.class}:${link.url}`}
                href={link.url}
                target="_blank"
                rel={link.sponsored ? 'noopener noreferrer sponsored' : 'noopener noreferrer'}
                className={`link-button ${link.class}`}
                onClick={link.sponsored ? () => trackAffiliateOutbound(game.slug, link.class) : undefined}
              >
                {link.label}
              </a>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
