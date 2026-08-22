import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../../lib/api'

function LegacyGlossary({ keywords }) {
  if (!keywords?.length) return null
  return (
    <div className="pro-card">
      <div className="pro-card-title">GLOSSARY</div>
      <div className="tag-list">
        {keywords.map((kw, i) => (
          <div key={`${kw.term}-${i}`} className="tag-item" title={kw.description}>{kw.term}</div>
        ))}
      </div>
    </div>
  )
}

export function ConceptGlossary({ slug, legacyKeywords = [] }) {
  const [entries, setEntries] = useState([])
  const [selectedId, setSelectedId] = useState(null)
  const [detail, setDetail] = useState(null)
  const [canonicalAvailable, setCanonicalAvailable] = useState(false)
  const [loadedSlug, setLoadedSlug] = useState(null)
  const hasGlossary = legacyKeywords.length > 0

  useEffect(() => {
    if (!hasGlossary) return undefined

    let cancelled = false
    api.get(`/api/games/${slug}/glossary?language_code=ja`)
      .then((data) => {
        if (cancelled) return
        const available = data?.status === 'available' && data.entries?.length > 0
        setEntries(available ? data.entries : [])
        setSelectedId(null)
        setDetail(null)
        setCanonicalAvailable(Boolean(available))
        setLoadedSlug(slug)
      })
      .catch(() => {
        if (cancelled) return
        setEntries([])
        setSelectedId(null)
        setDetail(null)
        setCanonicalAvailable(false)
        setLoadedSlug(slug)
      })

    return () => { cancelled = true }
  }, [slug, hasGlossary])

  const selected = useMemo(
    () => entries.find((entry) => entry.concept_id === selectedId) || null,
    [entries, selectedId],
  )

  const selectConcept = async (conceptId) => {
    if (selectedId === conceptId) {
      setSelectedId(null)
      setDetail(null)
      return
    }
    setSelectedId(conceptId)
    setDetail(null)
    try {
      const response = await api.get(`/api/concepts/${encodeURIComponent(conceptId)}`)
      setDetail(response)
    } catch {
      // The game glossary remains useful even if the deeper backlink view is unavailable.
    }
  }

  if (!hasGlossary || loadedSlug !== slug || !canonicalAvailable) {
    return <LegacyGlossary keywords={legacyKeywords} />
  }

  return (
    <div className="pro-card" aria-label="用語集">
      <div className="pro-card-title">GLOSSARY · LINKED VIEW</div>
      <div className="tag-list">
        {entries.map((entry) => (
          <button
            key={entry.concept_id}
            type="button"
            className="tag-item"
            aria-expanded={selectedId === entry.concept_id}
            onClick={() => selectConcept(entry.concept_id)}
            style={{ cursor: 'pointer', font: 'inherit' }}
          >
            {entry.label}
          </button>
        ))}
      </div>

      {selected && (
        <div
          role="region"
          aria-live="polite"
          aria-label={`${selected.label} の説明`}
          style={{ marginTop: '1rem', paddingTop: '1rem', borderTop: '1px solid var(--border)' }}
        >
          <div style={{ fontWeight: 700 }}>{selected.label}</div>
          <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: '2px' }}>
            {selected.concept_id}
          </div>
          {selected.definition && (
            <p style={{ margin: '0.75rem 0', lineHeight: 1.6 }}>{selected.definition}</p>
          )}
          {selected.aliases?.length > 0 && (
            <div className="game-empty-note">別名: {selected.aliases.join(' / ')}</div>
          )}
          {selected.related_concept_ids?.length > 0 && (
            <div style={{ marginTop: '0.75rem' }}>
              <strong style={{ fontSize: '0.78rem' }}>RELATED</strong>
              <div className="game-empty-note">{selected.related_concept_ids.join(' · ')}</div>
            </div>
          )}
          {selected.rule_references?.length > 0 && (
            <div style={{ marginTop: '0.75rem' }}>
              <strong style={{ fontSize: '0.78rem' }}>このゲームでは</strong>
              {selected.rule_references.map((reference) => (
                <div key={`${reference.rule_id}-${reference.reference_kind}`} className="game-empty-note" style={{ marginTop: '6px' }}>
                  {reference.normalized_statement}
                </div>
              ))}
            </div>
          )}
          {detail?.game_backlinks?.length > 0 && (
            <div style={{ marginTop: '0.75rem' }}>
              <strong style={{ fontSize: '0.78rem' }}>USED IN</strong>
              <div style={{ display: 'grid', gap: '6px', marginTop: '6px' }}>
                {detail.game_backlinks.map((backlink) => (
                  <Link key={backlink.game_id} to={`/games/${backlink.slug}`} className="back-link">
                    {backlink.title || backlink.slug}
                  </Link>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
