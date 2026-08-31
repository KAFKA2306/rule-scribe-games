import { useEffect } from 'react'
import ReactMarkdown from 'react-markdown'

function headingLabel(markdownText) {
  return markdownText
    .replace(/!\[([^\]]*)\]\([^)]*\)/g, '$1')
    .replace(/\[([^\]]+)\]\([^)]*\)/g, '$1')
    .replace(/[`*_~]/g, '')
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
  const occurrences = new Map()
  const sections = []

  markdown.split('\n').forEach((line, index) => {
    const match = /^(#{2,4})\s+(.+?)\s*#*\s*$/.exec(line)
    if (!match) return

    const level = match[1].length
    const label = headingLabel(match[2])
    if (!label) return

    const key = `${level}:${label.normalize('NFKC').toLowerCase()}`
    const occurrence = (occurrences.get(key) || 0) + 1
    occurrences.set(key, occurrence)

    sections.push({
      id: sectionId(label, occurrence),
      label,
      level,
      line: index + 1,
    })
  })

  return sections
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

function RuleMarkdown({ markdown = '' }) {
  const sections = getRuleSections(markdown)
  const headingComponents = createHeadingComponents(sections)

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
      )}
      <div className="markdown-content">
        <ReactMarkdown components={headingComponents}>{markdown}</ReactMarkdown>
      </div>
    </>
  )
}

export default RuleMarkdown
