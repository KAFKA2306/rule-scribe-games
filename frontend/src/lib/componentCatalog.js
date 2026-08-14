const SUPPORTED_VALUE_TYPES = new Set([
  'text',
  'integer',
  'number',
  'boolean',
  'enum',
  'concept_ref',
  'component_ref',
])

export const PAGE_SIZE = 100

export function getPropertyLabel(definition, languageCode = 'ja') {
  if (!definition) return ''
  return definition.labels?.[languageCode]
    || definition.labels?.en
    || definition.property_key
}

export function isSupportedDefinition(definition) {
  return Boolean(definition && SUPPORTED_VALUE_TYPES.has(definition.value_type))
}

export function getProperty(component, propertyKey) {
  return component?.properties?.find((property) => property.property_key === propertyKey) || null
}

export function getPropertyValues(component, propertyKey) {
  const property = getProperty(component, propertyKey)
  if (!property) return []
  return property.values
    ?.filter((entry) => entry && SUPPORTED_VALUE_TYPES.has(entry.value_type))
    .map((entry) => entry.value) ?? []
}

export function formatPropertyValue(value, definition) {
  if (value == null) return '—'
  if (!isSupportedDefinition(definition)) return '—'
  if (definition.value_type === 'boolean') return value ? 'YES' : 'NO'
  const suffix = definition.unit ? ` ${definition.unit}` : ''
  return `${String(value)}${suffix}`
}

export function propertyDisplayText(component, definition) {
  if (!isSupportedDefinition(definition)) return null
  const values = getPropertyValues(component, definition.property_key)
  if (values.length === 0) return null
  return values.map((value) => formatPropertyValue(value, definition)).join(' / ')
}

export function pageOffsets(total, pageSize = PAGE_SIZE) {
  if (!Number.isFinite(total) || total <= pageSize) return []
  const offsets = []
  for (let offset = pageSize; offset < total; offset += pageSize) offsets.push(offset)
  return offsets
}

function matchesPropertyFilter(component, definition, filterValue) {
  if (!isSupportedDefinition(definition)) return true
  if (filterValue == null || filterValue === '') return true
  const values = getPropertyValues(component, definition.property_key)
  if (values.length === 0) return false

  if (definition.value_type === 'integer' || definition.value_type === 'number') {
    const min = filterValue.min === '' || filterValue.min == null ? null : Number(filterValue.min)
    const max = filterValue.max === '' || filterValue.max == null ? null : Number(filterValue.max)
    return values.some((value) => {
      const numeric = Number(value)
      return Number.isFinite(numeric)
        && (min == null || numeric >= min)
        && (max == null || numeric <= max)
    })
  }

  if (definition.value_type === 'boolean') {
    if (filterValue !== 'true' && filterValue !== 'false') return true
    const expected = filterValue === 'true'
    return values.some((value) => Boolean(value) === expected)
  }

  const expected = String(filterValue).toLocaleLowerCase()
  if (definition.value_type === 'enum') {
    return values.some((value) => String(value) === String(filterValue))
  }
  return values.some((value) => String(value).toLocaleLowerCase().includes(expected))
}

function comparableValue(item, propertyKey) {
  if (propertyKey === 'canonical_name') return item.component.canonical_name.toLocaleLowerCase()
  const values = getPropertyValues(item.component, propertyKey)
  if (values.length === 0) return null
  return values[0]
}

export function filterAndSortComponentItems(
  items,
  definitions,
  {
    search = '',
    componentSetId = '',
    filters = {},
    sortKey = 'canonical_name',
    sortDirection = 'asc',
  } = {},
) {
  const definitionByKey = Object.fromEntries(
    definitions.filter(isSupportedDefinition).map((definition) => [definition.property_key, definition]),
  )
  const normalizedSearch = search.trim().toLocaleLowerCase()
  const filtered = items.filter((item) => {
    const component = item.component
    if (componentSetId && component.component_set_id !== componentSetId) return false
    if (normalizedSearch) {
      const haystack = [
        component.canonical_name,
        component.component_id,
        component.kind,
        ...component.properties.flatMap((property) => property.values.map((entry) => entry.value)),
      ].join(' ').toLocaleLowerCase()
      if (!haystack.includes(normalizedSearch)) return false
    }
    return Object.entries(filters).every(([propertyKey, filterValue]) => {
      const definition = definitionByKey[propertyKey]
      return definition ? matchesPropertyFilter(component, definition, filterValue) : true
    })
  })

  const direction = sortDirection === 'desc' ? -1 : 1
  return [...filtered].sort((left, right) => {
    const a = comparableValue(left, sortKey)
    const b = comparableValue(right, sortKey)
    if (a == null && b == null) return left.component.canonical_name.localeCompare(right.component.canonical_name)
    if (a == null) return 1
    if (b == null) return -1
    if (typeof a === 'number' && typeof b === 'number') return (a - b) * direction
    return String(a).localeCompare(String(b), undefined, { numeric: true }) * direction
  })
}

export function evidenceLabel(summary) {
  if (summary?.status === 'verified') return 'VERIFIED'
  if (summary?.status === 'contested') return 'CONTESTED'
  return 'UNVERIFIED'
}
