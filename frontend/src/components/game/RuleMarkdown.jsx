import { useEffect, useMemo, useState } from 'react'
import { useParams } from 'react-router-dom'
import ReactMarkdown from 'react-markdown'
import { api } from '../../lib/api'
import { getGlossaryData, glossaryConceptFragment, ruleReferenceSourceLabel } from './glossaryData'

const SOURCE_TYPE_LABELS = {
  rulebook: 'ルールブック',
  official_faq: '公式FAQ',
  official_errata: '公式エラッタ',
  official_clarification: '公式補足',
}

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

function ruleNodeId(ruleId) {
  return `rule-node-${ruleId}`
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

function trustedRuleReferences(entry) {
  return (entry.rule_references || [])
    .filter((reference) => ['verified', 'source_bound'].includes(reference.verification_status))
}

function glossaryEntrySearchText(entry) {
  return normalizeSearchText([
    entry.label,
    ...(entry.aliases || []),
    entry.definition,
  ].filter(Boolean).join(' '))
}

function matchingRuleReferences(entry, query) {
  const normalizedQuery = normalizeSearchText(query)
  if (!normalizedQuery) return []

  const tokens = normalizedQuery.split(' ').filter(Boolean)
  const entrySearchText = glossaryEntrySearchText(entry)
  return trustedRuleReferences(entry).filter((reference) => {
    const searchable = normalizeSearchText([
      entrySearchText,
      reference.normalized_statement,
      reference.player_count ? `${reference.player_count}人` : null,
      ruleReferenceSourceLabel(reference),
    ].filter(Boolean).join(' '))
    return tokens.every((token) => searchable.includes(token))
  })
}

function searchGlossary(entries, query) {
  const normalizedQuery = normalizeSearchText(query)
  if (!normalizedQuery) return []

  const tokens = normalizedQuery.split(' ').filter(Boolean)
  return entries.filter((entry) => {
    const entrySearchText = glossaryEntrySearchText(entry)
    if (tokens.every((token) => entrySearchText.includes(token))) return true
    return matchingRuleReferences(entry, query).length > 0
  })
}

function glossaryResultContext(entry, query) {
  const normalizedQuery = normalizeSearchText(query)
  const tokens = normalizedQuery.split(' ').filter(Boolean)
  const entrySearchText = glossaryEntrySearchText(entry)
  const referencesMatchingQuery = matchingRuleReferences(entry, query)
  const references = referencesMatchingQuery.length > 0
    ? referencesMatchingQuery
    : tokens.every((token) => entrySearchText.includes(token))
      ? trustedRuleReferences(entry)
      : []
  const sourceLabels = [...new Set(references.map(ruleReferenceSourceLabel).filter(Boolean))]
  const playerCounts = [...new Set(references.map((reference) => reference.player_count).filter(Boolean))]
  return {
    sourceLabels,
    playerCounts,
  }
}

function resultSnippet(section, query) {
  if (!section.body) return 'この見出しへ移動します。'

  const tokens = normalizeSearchText(query).split(' ').filter(Boolean)
  const sentences = section.body.match(/[^。！？!?]+[。！？!?]?/gu) || [section.body]
  const matchedSentences = sentences.filter((sentence) => {
    const normalizedSentence = normalizeSearchText(sentence)
    return tokens.some((token) => normalizedSentence.includes(token))
  })

  if (matchedSentences.length > 0) {
    return matchedSentences.slice(0, 2).join(' ').trim()
  }

  return section.body.length > 140 ? `${section.body.slice(0, 140)}…` : section.body
}

function sourceLabel(source) {
  return source.publisher_name || source.document_identity || source.source_id
}

function sourceTypeLabel(sourceType) {
  if (!sourceType) return '不明'
  return SOURCE_TYPE_LABELS[sourceType] || sourceType
}

function locatorLabel(locator) {
  if (!locator) return null
  return [
    locator.page_number ? `ページ ${locator.page_number}` : null,
    locator.section_heading ? `節 ${locator.section_heading}` : null,
    locator.anchor ? `位置 ${locator.anchor}` : null,
    locator.external_reference ? `参照 ${locator.external_reference}` : null,
  ].filter(Boolean).join(' / ') || null
}

function evidenceBindings(trace) {
  return (trace?.claims || []).flatMap((claimTrace) =>
    (claimTrace.bindings || []).map((detail) => ({
      ...detail,
      supportStatus: claimTrace.support_status,
      lifecycleStatus: claimTrace.claim?.lifecycle_status,
    })),
  )
}

function RuleEvidence({ slug, ruleNode }) {
  const [state, setState] = useState({ status: 'idle', data: null })

  const loadEvidence = () => {
    if (state.status !== 'idle') return
    setState({ status: 'loading', data: null })
    const params = new URLSearchParams({
      rule_set_id: ruleNode.rule_set_id,
      target_type: 'rule_node',
      rule_id: ruleNode.rule_id,
    })
    api.get(`/api/games/${encodeURIComponent(slug)}/evidence?${params.toString()}`)
      .then((data) => setState({ status: 'loaded', data }))
      .catch((error) => {
        console.error('Failed to fetch rule evidence:', error)
        setState({ status: 'error', data: null })
      })
  }

  const bindings = state.status === 'loaded' ? evidenceBindings(state.data) : []

  return (
    <details onToggle={(event) => { if (event.currentTarget.open) loadEvidence() }} style={{ marginTop: '0.4rem' }}>
      <summary>根拠を確認</summary>
      <div style={{ marginTop: '0.5rem' }}>
        {state.status === 'idle' && <div className="game-empty-note">開くと登録済みの根拠を取得します。</div>}
        {state.status === 'loading' && <div className="game-empty-note" role="status">根拠を取得しています...</div>}
        {state.status === 'error' && (
          <div className="game-empty-note" role="alert">根拠を取得できませんでした。</div>
        )}
        {state.status === 'loaded' && bindings.length === 0 && (
          <div className="game-empty-note">このルールの根拠は登録されていません。</div>
        )}
        {state.status === 'loaded' && bindings.length > 0 && (
          <ul aria-label="このルールの根拠" style={{ margin: 0, paddingInlineStart: '1.25rem' }}>
            {bindings.map(({ binding, source, locator, supportStatus, lifecycleStatus }) => (
              <li key={binding.binding_id} style={{ marginBlock: '0.5rem' }}>
                <div>
                  {source.source_url
                    ? <a href={source.source_url} target="_blank" rel="noreferrer">{sourceLabel(source)}</a>
                    : <strong>{sourceLabel(source)}</strong>}
                </div>
                <div className="game-empty-note" style={{ marginTop: '0.2rem' }}>
                  資料: {sourceTypeLabel(source.source_type)}
                  {source.revision_label ? ` / 改訂: ${source.revision_label}` : ''}
                  {source.language_code ? ` / 言語: ${source.language_code}` : ''}
                  {source.platform ? ` / プラットフォーム: ${source.platform}` : ''}
                </div>
                {locatorLabel(locator) && (
                  <div className="game-empty-note" style={{ marginTop: '0.2rem' }}>位置: {locatorLabel(locator)}</div>
                )}
                <div className="game-empty-note" style={{ marginTop: '0.2rem' }}>
                  関係: {binding.relation} / Claim: {lifecycleStatus} / 根拠状態: {supportStatus}
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </details>
  )
}

function RuleMarkdown({ markdown = '', ruleNodes = [] }) {
  const { slug } = useParams()
  const [query, setQuery] = useState('')
  const [glossaryEntries, setGlossaryEntries] = useState([])
  const [glossaryStatus, setGlossaryStatus] = useState('loading')
  const [glossarySlug, setGlossarySlug] = useState(null)
  const sections = useMemo(() => getRuleSections(markdown), [markdown])
  const sectionResults = useMemo(() => searchSections(sections, query), [sections, query])
  const currentGlossaryEntries = glossarySlug === slug ? glossaryEntries : []
  const glossaryResults = useMemo(() => searchGlossary(currentGlossaryEntries, query), [currentGlossaryEntries, query])
  const headingComponents = useMemo(() => createHeadingComponents(sections), [sections])
  const hasQuery = normalizeSearchText(query).length > 0
  const resultCount = sectionResults.length + glossaryResults.length

  useEffect(() => {
    let cancelled = false

    getGlossaryData(slug, 'ja')
      .then((data) => {
        if (cancelled) return
        const available = data?.status === 'available' && data.entries?.length > 0
        setGlossaryEntries(available ? data.entries : [])
        setGlossaryStatus(available ? 'available' : 'unavailable')
        setGlossarySlug(slug)
      })
      .catch(() => {
        if (cancelled) return
        setGlossaryEntries([])
        setGlossaryStatus('error')
        setGlossarySlug(slug)
      })

    return () => { cancelled = true }
  }, [slug])

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
  }, [markdown, ruleNodes])

  return (
    <>
      {ruleNodes.length > 0 && (
        <section className="pro-card" aria-labelledby="canonical-rule-nodes-title" style={{ marginBottom: '1rem' }}>
          <div id="canonical-rule-nodes-title" className="pro-card-title">確認済みルール</div>
          <div className="game-empty-note" style={{ marginBottom: '0.6rem' }}>
            選択した用語に関連する、現在のRuleSetの確認済みルールです。
          </div>
          <ul style={{ margin: 0, paddingInlineStart: '1.25rem' }}>
            {ruleNodes.map((ruleNode) => (
              <li
                key={`${ruleNode.rule_set_id}:${ruleNode.rule_id}`}
                id={ruleNodeId(ruleNode.rule_id)}
                tabIndex={-1}
                style={{ marginBlock: '0.6rem', scrollMarginTop: '1rem' }}
              >
                <div>{ruleNode.text}</div>
                <RuleEvidence slug={slug} ruleNode={ruleNode} />
              </li>
            ))}
          </ul>
        </section>
      )}

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
              placeholder="例: 得点、2人、Mermaid、Bid"
              autoComplete="off"
              style={{ width: '100%', maxWidth: '36rem' }}
            />
            {hasQuery && (
              <div style={{ marginTop: '0.75rem' }}>
                <div role="status" aria-live="polite" style={{ marginBottom: '0.5rem' }}>
                  {resultCount > 0 ? `${resultCount}件見つかりました` : '該当するルールは見つかりませんでした'}
                </div>
                {sectionResults.length > 0 && (
                  <ul style={{ margin: 0, paddingInlineStart: '1.25rem' }}>
                    {sectionResults.map((section) => (
                      <li key={section.id} style={{ marginBlock: '0.6rem' }}>
                        <a href={`#${section.id}`}><strong>{section.label}</strong></a>
                        <div style={{ marginTop: '0.2rem' }}>{resultSnippet(section, query)}</div>
                      </li>
                    ))}
                  </ul>
                )}
                {glossaryResults.length > 0 && (
                  <ul aria-label="用語集の検索結果" style={{ margin: '0.75rem 0 0', paddingInlineStart: '1.25rem' }}>
                    {glossaryResults.map((entry) => {
                      const context = glossaryResultContext(entry, query)
                      return (
                        <li key={entry.concept_id} style={{ marginBlock: '0.6rem' }}>
                          <a href={glossaryConceptFragment(entry.concept_id)}><strong>{entry.label}</strong></a>
                          {entry.aliases?.length > 0 && (
                            <div className="game-empty-note" style={{ marginTop: '0.2rem' }}>別名: {entry.aliases.join(' / ')}</div>
                          )}
                          {context.sourceLabels.length > 0 && (
                            <div className="game-empty-note" style={{ marginTop: '0.2rem' }}>
                              出典: {context.sourceLabels.join(' / ')}
                            </div>
                          )}
                          {context.playerCounts.length > 0 && (
                            <div className="game-empty-note" style={{ marginTop: '0.2rem' }}>
                              人数条件: {context.playerCounts.map((count) => `${count}人`).join(' / ')}
                            </div>
                          )}
                        </li>
                      )
                    })}
                  </ul>
                )}
                {glossarySlug === slug && glossaryStatus === 'error' && (
                  <div className="game-empty-note" role="alert" style={{ marginTop: '0.75rem' }}>
                    用語集の正準データを取得できないため、本文だけを検索しています。
                  </div>
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