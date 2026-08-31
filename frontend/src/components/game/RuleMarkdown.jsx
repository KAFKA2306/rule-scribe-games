import { useEffect, useMemo, useState } from 'react'
import ReactMarkdown from 'react-markdown'

function headingLabel(markdownText) {
  return markdownText
    .replace(/!\[([^\]]*)\]\([^)]*\)/g, '$1')
    .replace(/\[([^\]]+)\]\([^)]*\)/g, '$1')
    .replace(/[`*_~]/g, '')
    .trim()
}

function plainText(markdownText) {
  return markdownText
    .replace(/!\[([^\]]*)\]\([^)]*\)/g, '$1')
    .replace(/\[([^\]]+)\]\([^)]*\)/g, '$1')
    .replace(/[`*_~>#-]/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()
}

function normalizeSearchText(value) {
  return String(value || '')
    .normalize('NFKC')
    .toLowerCase()
    .replace(/\s+/g, ' ')
    .trim()
}

function sectionSlug(label) {
  return label
    .normalize('NFKC')
    .toLowerCase()
    .replace(/[\s/]+/g, '-')
    .replace(/[^\p{L}\p{N}_-]+/gu, '')
    .replace(/-+/g, '-')
    .replace(/^-|-$/g, '') || 'section'
}

function sectionId(label, occurrence = 1) {
  const base = `rule-${sectionSlug(label)}`
  return occurrence === 1 ? base : `${base}-${occurrence}`
}

function getRuleSections(markdown = '') {
  const lines = markdown.split('\n')
  const occurrences = new Map()
  const headings = []

  lines.forEach((line, index) => {
    const match = /^(#{2,4})\s+(.+?)\s*#*\s*$/.exec(line)
    if (!match) return

    const level = match[1].length
    const label = headingLabel(match[2])
    if (!label) return

    const key = `${level}:${label.normalize('NFKC').toLowerCase()}`
    const occurrence = (occurrences.get(key) || 0) + 1
    occurrences.set(key, occurrence)

    headings.push({
      id: sectionId(label, occurrence),
      label,
      level,
      line: index + 1,
      lineIndex: index,
    })
  })

  return headings.map((heading, index) => {
    const nextHeading = headings[index + 1]
    const bodyLines = lines.slice(heading.lineIndex + 1, nextHeading?.lineIndex ?? lines.length)
    const body = plainText(bodyLines.join('\n'))
    return {
      ...heading,
      body,
      searchText: normalizeSearchText(`${heading.label} ${body}`),
    }
  })
}

function createHeadingComponents(sections) {
  const renderHeading = (level) => {
    const Tag = `h${level}`
    return function RuleHeading({ children, node }) {
      const line = node?.position?.start?.line
      const section = sections.find((item) => item.level === level && item.line === line)
      const id = section?.id

      return (
        <Tag id={id} tabIndex={id ? -1 : undefined} style={id ? { scrollMarginTop: '1rem' } : undefined}>
          {children}
        </Tag>
      )
    }
  }

  return {
    h2: renderHeading(2),
    h3: renderHeading(3),
    h4: renderHeading(4),
  }
}

function decodedHash() {
  if (typeof window === 'undefined') return ''
  try {
    return decodeURIComponent(window.location.hash.slice(1))
  } catch {
    return ''
  }
}

function searchSections(sections, query) {
  const normalizedQuery = normalizeSearchText(query)
  if (!normalizedQuery) return []

  const tokens = normalizedQuery.split(' ').filter(Boolean)
  return sections.filter((section) => tokens.every((token) => section.searchText.includes(token)))
}

function resultSnippet(section) {
  if (!section.body) return 'この見出しへ移動します。'
  return section.body.length > 140 ? `${section.body.slice(0, 140)}…` : section.body
}

function RuleMarkdown({ markdown = '' }) {
  const [query, setQuery] = useState('')
  const sections = useMemo(() => getRuleSections(markdown), [markdown])
  const results = useMemo(() => searchSections(sections, query), [sections, query])
  const headingComponents = useMemo(() => createHeadingComponents(sections), [sections])
  const hasQuery = normalizeSearchText(query).length > 0

  useEffect(() => {
    const focusCurrentSection = () => {
      const id = decodedHash()
      if (!id.startsWith('rule-')) return

      window.requestAnimationFrame(() => {
        const target = document.getElementById(id)
        if (!target) return
        target.scrollIntoView({ block: 'start' })
        target.focus({ preventScroll: true })
      })
    }

    focusCurrentSection()
    window.addEventListener('hashchange', focusCurrentSection)
    window.addEventListener('popstate', focusCurrentSection)
    return () => {
      window.removeEventListener('hashchange', focusCurrentSection)
      window.removeEventListener('popstate', focusCurrentSection)
    }
  }, [markdown])

  return (
    <>
      {sections.length > 0 && (
        <>
          <section className="pro-card" aria-labelledby="rule-lookup-title" style={{ marginBottom: '1rem' }}>
            <div id="rule-lookup-title" className="pro-card-title">ルール内を検索</div>
            <label htmlFor="rule-lookup-input" style={{ display: 'block', marginBottom: '0.4rem' }}>
              裁定・用語を入力
            </label>
            <input
              id="rule-lookup-input"
              type="search"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="例: 得点、2人、Mermaid"
              autoComplete="off"
              style={{ width: '100%', maxWidth: '36rem' }}
            />
            {hasQuery && (
              <div style={{ marginTop: '0.75rem' }}>
                <div role="status" aria-live="polite" style={{ marginBottom: '0.5rem' }}>
                  {results.length > 0 ? `${results.length}件見つかりました` : '該当するルールは見つかりませんでした'}
                </div>
                {results.length > 0 && (
                  <ul style={{ margin: 0, paddingInlineStart: '1.25rem' }}>
                    {results.map((section) => (
                      <li key={section.id} style={{ marginBlock: '0.6rem' }}>
                        <a href={`#${section.id}`}><strong>{section.label}</strong></a>
                        <div style={{ marginTop: '0.2rem' }}>{resultSnippet(section)}</div>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            )}
          </section>

          <nav className="pro-card" aria-label="ルール内の見出し" style={{ marginBottom: '1rem' }}>
            <div className="pro-card-title">ルール内の見出し</div>
            <ul style={{ margin: 0, paddingInlineStart: '1.25rem' }}>
              {sections.map((section) => (
                <li key={section.id} style={{ marginBlock: '0.35rem' }}>
                  <a href={`#${section.id}`}>{section.label}</a>
                </li>
              ))}
            </ul>
          </nav>
        </>
      )}
      <div className="markdown-content">
        <ReactMarkdown components={headingComponents}>{markdown}</ReactMarkdown>
      </div>
    </>
  )
}

export default RuleMarkdown