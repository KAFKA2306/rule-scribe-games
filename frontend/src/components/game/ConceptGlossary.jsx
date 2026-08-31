import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../../lib/api'

function normalizeSearchText(value) {
  return String(value || '')
    .normalize('NFKC')
    .toLowerCase()
    .replace(/\s+/g, ' ')
    .trim()
}

function isVerifiedRuleReference(reference) {
  return reference?.verification_status === 'source_bound' || reference?.verification_status === 'verified'
}

export function ConceptGlossary({ slug }) {
  const [entries, setEntries] = useState([])
  const [query, setQuery] = useState('')
  const [selectedId, setSelectedId] = useState(null)
  const [detail, setDetail] = useState(null)
  const [fetchStatus, setFetchStatus] = useState('loading')
  const [loadedSlug, setLoadedSlug] = useState(null)
  const [detailError, setDetailError] = useState(false)

  useEffect(() => {
    let cancelled = false

    api.get(`/api/games/${slug}/glossary?language_code=ja`)
      .then((data) => {
        if (cancelled) return
        const available = data?.status === 'available' && data.entries?.length > 0
        setEntries(available ? data.entries : [])
        setFetchStatus(available ? 'available' : 'unavailable')
        setLoadedSlug(slug)
      })
      .catch(() => {
        if (cancelled) return
        setEntries([])
        setFetchStatus('error')
        setLoadedSlug(slug)
      })

    return () => { cancelled = true }
  }, [slug])

  const normalizedQuery = normalizeSearchText(query)
  const filteredEntries = useMemo(() => {
    if (!normalizedQuery) return entries
    const tokens = normalizedQuery.split(' ').filter(Boolean)
    return entries.filter((entry) => {
      const searchable = normalizeSearchText([
        entry.label,
        ...(entry.aliases || []),
      ].join(' '))
      return tokens.every((token) => searchable.includes(token))
    })
  }, [entries, normalizedQuery])

  const selected = useMemo(
    () => entries.find((entry) => entry.concept_id === selectedId) || null,
    [entries, selectedId],
  )
  const verifiedRuleReferences = useMemo(
    () => selected?.rule_references?.filter(isVerifiedRuleReference) || [],
    [selected],
  )

  const selectConcept = async (conceptId) => {
    if (selectedId === conceptId) {
      setSelectedId(null)
      setDetail(null)
      setDetailError(false)
      return
    }
    setSelectedId(conceptId)
    setDetail(null)
    setDetailError(false)
    try {
      const response = await api.get(`/api/concepts/${encodeURIComponent(conceptId)}`)
      setDetail(response)
    } catch {
      setDetailError(true)
    }
  }

  if (loadedSlug !== slug) {
    return (
      <div className="pro-card" aria-label="用語集">
        <div className="pro-card-title">GLOSSARY</div>
        <div className="game-empty-state" role="status">用語集を確認しています...</div>
      </div>
    )
  }

  if (fetchStatus === 'error') {
    return (
      <div className="pro-card" aria-label="用語集">
        <div className="pro-card-title">GLOSSARY</div>
        <div className="game-empty-state" role="alert">用語集の正準データを取得できませんでした。</div>
      </div>
    )
  }

  if (fetchStatus === 'unavailable') {
    return (
      <div className="pro-card" aria-label="用語集">
        <div className="pro-card-title">GLOSSARY</div>
        <div className="game-empty-state">用語集の正準データは未整備です。</div>
      </div>
    )
  }

  return (
    <div className="pro-card" aria-label="用語集">
      <div className="pro-card-title">GLOSSARY · LINKED VIEW</div>
      <label htmlFor={`glossary-search-${slug}`} style={{ display: 'block', marginBottom: '0.4rem' }}>
        用語集を検索
      </label>
      <input
        id={`glossary-search-${slug}`}
        type="search"
        value={query}
        onChange={(event) => setQuery(event.target.value)}
        placeholder="用語・別名を入力"
        autoComplete="off"
        style={{ width: '100%', marginBottom: '0.75rem' }}
      />
      {normalizedQuery && (
        <div role="status" aria-live="polite" className="game-empty-note" style={{ marginBottom: '0.75rem' }}>
          {filteredEntries.length > 0
            ? `${filteredEntries.length}件の用語が見つかりました`
            : '該当する用語は見つかりませんでした'}
        </div>
      )}
      {filteredEntries.length > 0 && (
        <div className="tag-list">
          {filteredEntries.map((entry) => (
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
      )}

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
          {verifiedRuleReferences.length > 0 && (
            <div style={{ marginTop: '0.75rem' }}>
              <strong style={{ fontSize: '0.78rem' }}>このゲームでは</strong>
              {verifiedRuleReferences.map((reference) => (
                <div key={`${reference.rule_id}-${reference.reference_kind}`} className="game-empty-note" style={{ marginTop: '6px' }}>
                  <div>{reference.normalized_statement}</div>
                  {reference.source_url && (
                    <a href={reference.source_url} target="_blank" rel="noreferrer" style={{ display: 'inline-block', marginTop: '4px' }}>
                      出典を確認
                    </a>
                  )}
                </div>
              ))}
            </div>
          )}
          {selected.rule_references?.length > 0 && verifiedRuleReferences.length === 0 && (
            <div className="game-empty-note" style={{ marginTop: '0.75rem' }}>
              確認済みの関連ルールはありません。
            </div>
          )}
          {detailError && (
            <div className="game-empty-note" role="alert" style={{ marginTop: '0.75rem' }}>
              この用語の関連ゲーム情報を取得できませんでした。
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
