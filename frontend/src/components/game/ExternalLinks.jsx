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

export const ExternalLinks = ({ game }) => {
  const { affiliate_urls, official_url, bgg_url, amazon_url } = game
  const amazon = affiliate_urls?.amazon || amazon_url
  const rakuten = affiliate_urls?.rakuten
  const yahoo = affiliate_urls?.yahoo

  const links = [
    { url: amazon, label: 'Amazon', class: 'amazon' },
    { url: rakuten, label: '楽天で見る', class: 'rakuten' },
    { url: yahoo, label: 'Yahoo!で見る', class: 'yahoo' },
    { url: official_url, label: '公式サイト', class: 'official' },
    { url: bgg_url, label: 'BoardGameGeek', class: 'bgg' },
    { url: game.bga_url, label: 'Board Game Arena', class: 'bga' },
  ].filter((link) => isValidUrl(link.url))

  if (links.length === 0) return null

  return (
    <div className="info-section">
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
    </div>
  )
}
