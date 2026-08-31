import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../../lib/api'

export function ConceptGlossary({ slug }) {
  const [entries, setEntries] = useState([])
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

  const selected = useMemo(
    () => entries.find((entry) => entry.concept_id === selectedId) || null,
    [entries, selectedId],
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
