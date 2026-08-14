import { useEffect, useMemo, useState } from 'react'
import { api } from '../../lib/api'
import {
  PAGE_SIZE,
  evidenceLabel,
  filterAndSortComponentItems,
  getPropertyLabel,
  isSupportedDefinition,
  pageOffsets,
  propertyDisplayText,
} from '../../lib/componentCatalog'
import './components-panel.css'

function rulesetLabel(ruleset) {
  if (!ruleset) return ''
  return [
    ruleset.edition_label,
    ruleset.platform,
    ruleset.language_code,
    ruleset.revision_label,
  ].filter(Boolean).join(' · ') || ruleset.ruleset_id
}

function EvidenceBadge({ summary }) {
  const label = evidenceLabel(summary)
  return <span className={`component-evidence component-evidence--${summary?.status || 'unknown'}`}>{label}</span>
}

function PropertyFilter({ definition, value, onChange, languageCode }) {
  const label = getPropertyLabel(definition, languageCode)
  if (!definition.filterable || !isSupportedDefinition(definition)) return null

  if (definition.value_type === 'enum') {
    return (
      <label className="component-filter">
        <span>{label}</span>
        <select value={value || ''} onChange={(event) => onChange(event.target.value)}>
          <option value="">すべて</option>
          {definition.enum_values?.map((option) => <option key={option} value={option}>{option}</option>)}
        </select>
      </label>
    )
  }

  if (definition.value_type === 'boolean') {
    return (
      <label className="component-filter">
        <span>{label}</span>
        <select value={value || ''} onChange={(event) => onChange(event.target.value)}>
          <option value="">すべて</option>
          <option value="true">YES</option>
          <option value="false">NO</option>
        </select>
      </label>
    )
  }

  if (definition.value_type === 'integer' || definition.value_type === 'number') {
    const numeric = value || { min: '', max: '' }
    return (
      <fieldset className="component-filter component-filter--range">
        <legend>{label}</legend>
        <label>
          <span className="sr-only">{label} 最小値</span>
          <input
            type="number"
            inputMode="decimal"
            placeholder="MIN"
            value={numeric.min ?? ''}
            onChange={(event) => onChange({ ...numeric, min: event.target.value })}
          />
        </label>
        <span aria-hidden="true">–</span>
        <label>
          <span className="sr-only">{label} 最大値</span>
          <input
            type="number"
            inputMode="decimal"
            placeholder="MAX"
            value={numeric.max ?? ''}
            onChange={(event) => onChange({ ...numeric, max: event.target.value })}
          />
        </label>
      </fieldset>
    )
  }

  return (
    <label className="component-filter">
      <span>{label}</span>
      <input
        type="search"
        value={value || ''}
        onChange={(event) => onChange(event.target.value)}
        placeholder={`${label}で絞る`}
      />
    </label>
  )
}

function PropertyRows({ item, definitions, languageCode, slug, ruleSetId }) {
  const definitionByKey = Object.fromEntries(definitions.map((definition) => [definition.property_key, definition]))
  return item.component.properties.map((property) => {
    const definition = definitionByKey[property.property_key]
    if (!isSupportedDefinition(definition)) return null
    const text = propertyDisplayText(item.component, definition)
    if (text == null) return null
    const evidence = item.property_evidence?.[property.property_key]
    const claimId = evidence?.claim_ids?.[0]
    const evidenceHref = claimId
      ? `/api/games/${encodeURIComponent(slug)}/claims/${encodeURIComponent(claimId)}?rule_set_id=${encodeURIComponent(ruleSetId)}`
      : null
    return (
      <div className="component-detail-property" key={property.property_key}>
        <dt>{getPropertyLabel(definition, languageCode)}</dt>
        <dd>
          <span>{text}</span>
          <EvidenceBadge summary={evidence} />
          {evidenceHref && (
            <a href={evidenceHref} target="_blank" rel="noreferrer" className="component-trace-link">
              EVIDENCE
            </a>
          )}
        </dd>
      </div>
    )
  })
}

function ComponentDetail({ item, definitions, componentSets, languageCode, slug, ruleSetId, onClose }) {
  const component = item.component
  const setName = componentSets.find((set) => set.component_set_id === component.component_set_id)?.canonical_name

  return (
    <section className="component-detail" role="dialog" aria-modal="false" aria-labelledby="component-detail-title">
      <div className="component-detail-header">
        <div>
          <div className="component-kicker">{component.kind.toUpperCase()} · {setName || 'UNGROUPED'}</div>
          <h3 id="component-detail-title">{component.canonical_name}</h3>
          <code>{component.component_id}</code>
        </div>
        <button type="button" className="component-detail-close" onClick={onClose} aria-label="コンポーネント詳細を閉じる">×</button>
      </div>

      <dl className="component-detail-properties">
        <PropertyRows
          item={item}
          definitions={definitions}
          languageCode={languageCode}
          slug={slug}
          ruleSetId={ruleSetId}
        />
      </dl>

      {component.abilities?.length > 0 && (
        <div className="component-detail-section">
          <h4>ABILITIES</h4>
          {component.abilities.map((ability) => {
            const evidence = item.ability_evidence?.[ability.ability_id]
            const printedClaimId = evidence?.printed_text?.claim_ids?.[0]
            const normalizedClaimId = evidence?.normalized?.claim_ids?.[0]
            return (
              <article className="component-ability" key={ability.ability_id}>
                <div className="component-ability-title">
                  <strong>{ability.normalized_label || ability.ability_id}</strong>
                  <EvidenceBadge summary={evidence?.normalized} />
                </div>
                {ability.printed_text && (
                  <p>
                    {ability.printed_text} <EvidenceBadge summary={evidence?.printed_text} />
                  </p>
                )}
                <div className="component-detail-links">
                  {[printedClaimId, normalizedClaimId].filter(Boolean).map((claimId) => (
                    <a
                      key={claimId}
                      href={`/api/games/${encodeURIComponent(slug)}/claims/${encodeURIComponent(claimId)}?rule_set_id=${encodeURIComponent(ruleSetId)}`}
                      target="_blank"
                      rel="noreferrer"
                    >
                      EVIDENCE {claimId}
                    </a>
                  ))}
                </div>
              </article>
            )
          })}
        </div>
      )}

      {component.concept_ids?.length > 0 && (
        <div className="component-detail-section">
          <h4>CONCEPTS</h4>
          <div className="component-detail-links">
            {component.concept_ids.map((conceptId) => (
              <a key={conceptId} href={`/api/concepts/${encodeURIComponent(conceptId)}`} target="_blank" rel="noreferrer">
                {conceptId}
              </a>
            ))}
          </div>
        </div>
      )}

      {component.rule_ids?.length > 0 && (
        <div className="component-detail-section">
          <h4>RULE REFERENCES</h4>
          <div className="component-detail-links">
            {component.rule_ids.map((ruleId) => (
              <a
                key={ruleId}
                href={`/api/games/${encodeURIComponent(slug)}/evidence?rule_set_id=${encodeURIComponent(ruleSetId)}&target_type=rule_node&rule_id=${encodeURIComponent(ruleId)}`}
                target="_blank"
                rel="noreferrer"
              >
                {ruleId}
              </a>
            ))}
          </div>
        </div>
      )}
    </section>
  )
}

export function ComponentsPanel({ slug, ruleSetIds, languageCode = 'ja' }) {
  const [selectedRuleSetId, setSelectedRuleSetId] = useState(ruleSetIds[0] || '')
  const [rulesets, setRulesets] = useState([])
  const [componentSets, setComponentSets] = useState([])
  const [definitions, setDefinitions] = useState([])
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [search, setSearch] = useState('')
  const [componentSetId, setComponentSetId] = useState('')
  const [filters, setFilters] = useState({})
  const [sortKey, setSortKey] = useState('canonical_name')
  const [sortDirection, setSortDirection] = useState('asc')
  const [selectedComponentId, setSelectedComponentId] = useState(null)

  useEffect(() => {
    setSelectedRuleSetId((current) => ruleSetIds.includes(current) ? current : (ruleSetIds[0] || ''))
  }, [ruleSetIds])

  useEffect(() => {
    let cancelled = false
    if (ruleSetIds.length <= 1) {
      setRulesets([])
      return () => { cancelled = true }
    }
    api.get(`/api/games/${encodeURIComponent(slug)}/rule-sets`)
      .then((payload) => {
        if (!cancelled) setRulesets((payload.rulesets || []).filter((ruleset) => ruleSetIds.includes(ruleset.ruleset_id)))
      })
      .catch((err) => {
        if (!cancelled) console.error('Failed to load component RuleSets:', err)
      })
    return () => { cancelled = true }
  }, [slug, ruleSetIds])

  useEffect(() => {
    let cancelled = false
    if (!selectedRuleSetId) {
      setLoading(false)
      return () => { cancelled = true }
    }

    const loadCatalog = async () => {
      setLoading(true)
      setError(null)
      setSelectedComponentId(null)
      try {
        const base = `/api/games/${encodeURIComponent(slug)}/component-catalog?rule_set_id=${encodeURIComponent(selectedRuleSetId)}&limit=${PAGE_SIZE}`
        const first = await api.get(`${base}&offset=0`)
        if (cancelled) return
        if (first.status !== 'available') {
          setItems([])
          setComponentSets([])
          setDefinitions([])
          return
        }
        const offsets = pageOffsets(first.total, PAGE_SIZE)
        const rest = await Promise.all(offsets.map((offset) => api.get(`${base}&offset=${offset}`)))
        if (cancelled) return
        setComponentSets(first.component_sets || [])
        setDefinitions(first.property_definitions || [])
        setItems([...(first.items || []), ...rest.flatMap((page) => page.items || [])])
        setComponentSetId('')
        setFilters({})
        setSortKey('canonical_name')
        setSortDirection('asc')
      } catch (err) {
        if (!cancelled) {
          console.error(err)
          setError('コンポーネント情報の取得に失敗しました')
        }
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    loadCatalog()
    return () => { cancelled = true }
  }, [slug, selectedRuleSetId])

  const filterableDefinitions = useMemo(
    () => definitions.filter((definition) => definition.filterable && isSupportedDefinition(definition)),
    [definitions],
  )
  const sortableDefinitions = useMemo(
    () => definitions.filter((definition) => definition.sortable && isSupportedDefinition(definition)),
    [definitions],
  )
  const visibleItems = useMemo(
    () => filterAndSortComponentItems(items, definitions, {
      search,
      componentSetId,
      filters,
      sortKey,
      sortDirection,
    }),
    [items, definitions, search, componentSetId, filters, sortKey, sortDirection],
  )
  const selectedItem = items.find((item) => item.component.component_id === selectedComponentId) || null

  if (loading) return <div className="component-panel-state" role="status">COMPONENT CATALOG LOADING...</div>
  if (error) return <div className="component-panel-state component-panel-state--error" role="alert">{error}</div>

  return (
    <section className="components-panel" aria-labelledby="components-panel-title">
      <div className="components-panel-heading">
        <div>
          <div className="component-kicker">CANONICAL COMPONENT CATALOG</div>
          <h2 id="components-panel-title">COMPONENTS</h2>
          <p>カード・タイル・トークン等を同じschemaから表示します。検証状態はfield-level evidenceに基づきます。</p>
        </div>
        <div className="component-count" aria-live="polite">{visibleItems.length} / {items.length}</div>
      </div>

      {ruleSetIds.length > 1 && (
        <label className="component-ruleset-select">
          <span>RULESET</span>
          <select value={selectedRuleSetId} onChange={(event) => setSelectedRuleSetId(event.target.value)}>
            {ruleSetIds.map((id) => {
              const ruleset = rulesets.find((entry) => entry.ruleset_id === id)
              return <option value={id} key={id}>{rulesetLabel(ruleset) || id}</option>
            })}
          </select>
        </label>
      )}

      <div className="component-controls" aria-label="コンポーネントの検索と絞り込み">
        <label className="component-filter component-filter--search">
          <span>SEARCH</span>
          <input type="search" value={search} onChange={(event) => setSearch(event.target.value)} placeholder="名前・ID・属性を検索" />
        </label>

        {componentSets.length > 1 && (
          <label className="component-filter">
            <span>GROUP</span>
            <select value={componentSetId} onChange={(event) => setComponentSetId(event.target.value)}>
              <option value="">すべて</option>
              {componentSets.map((set) => <option key={set.component_set_id} value={set.component_set_id}>{set.canonical_name}</option>)}
            </select>
          </label>
        )}

        {filterableDefinitions.map((definition) => (
          <PropertyFilter
            key={definition.property_key}
            definition={definition}
            value={filters[definition.property_key]}
            languageCode={languageCode}
            onChange={(value) => setFilters((current) => ({ ...current, [definition.property_key]: value }))}
          />
        ))}

        <label className="component-filter">
          <span>SORT</span>
          <select value={sortKey} onChange={(event) => setSortKey(event.target.value)}>
            <option value="canonical_name">NAME</option>
            {sortableDefinitions.map((definition) => (
              <option value={definition.property_key} key={definition.property_key}>{getPropertyLabel(definition, languageCode)}</option>
            ))}
          </select>
        </label>

        <label className="component-filter">
          <span>DIRECTION</span>
          <select value={sortDirection} onChange={(event) => setSortDirection(event.target.value)}>
            <option value="asc">ASC</option>
            <option value="desc">DESC</option>
          </select>
        </label>
      </div>

      {visibleItems.length === 0 ? (
        <div className="component-panel-state" role="status">条件に一致するコンポーネントはありません。</div>
      ) : (
        <div className="component-grid" role="list" aria-label="コンポーネント一覧">
          {visibleItems.map((item) => {
            const component = item.component
            const setName = componentSets.find((set) => set.component_set_id === component.component_set_id)?.canonical_name
            const previewDefinitions = definitions.filter((definition) => propertyDisplayText(component, definition) != null).slice(0, 3)
            return (
              <article className="component-card" role="listitem" key={component.component_id}>
                <button
                  type="button"
                  className="component-card-button"
                  onClick={() => setSelectedComponentId(component.component_id)}
                  aria-expanded={selectedComponentId === component.component_id}
                  aria-controls="component-detail-panel"
                >
                  <div className="component-card-meta">
                    <span>{component.kind.toUpperCase()}</span>
                    <span>{setName || 'UNGROUPED'}</span>
                  </div>
                  <h3>{component.canonical_name}</h3>
                  <code>{component.component_id}</code>
                  {component.quantity != null && <div className="component-quantity">QTY {component.quantity}</div>}
                  <dl className="component-card-properties">
                    {previewDefinitions.map((definition) => (
                      <div key={definition.property_key}>
                        <dt>{getPropertyLabel(definition, languageCode)}</dt>
                        <dd>
                          {propertyDisplayText(component, definition)}
                          <EvidenceBadge summary={item.property_evidence?.[definition.property_key]} />
                        </dd>
                      </div>
                    ))}
                  </dl>
                </button>
              </article>
            )
          })}
        </div>
      )}

      <div id="component-detail-panel">
        {selectedItem && (
          <ComponentDetail
            item={selectedItem}
            definitions={definitions}
            componentSets={componentSets}
            languageCode={languageCode}
            slug={slug}
            ruleSetId={selectedRuleSetId}
            onClose={() => setSelectedComponentId(null)}
          />
        )}
      </div>
    </section>
  )
}
