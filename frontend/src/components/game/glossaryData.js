import { api } from '../../lib/api'

const glossaryRequests = new Map()

export function isVerifiedRuleReference(reference) {
  return reference?.verification_status === 'source_bound' || reference?.verification_status === 'verified'
}

export function ruleReferenceSourceLabel(reference) {
  const locator = String(reference?.source_locator || '')
  if (locator.includes(':rulebook:')) return 'ルールブック'
  if (locator.includes(':faq:')) return 'FAQ'
  return null
}

export function getGlossaryData(slug, languageCode = 'ja') {
  if (!slug) return Promise.resolve({ status: 'not_available', entries: [] })

  const key = `${slug}:${languageCode}`
  if (!glossaryRequests.has(key)) {
    glossaryRequests.set(
      key,
      api.get(`/api/games/${slug}/glossary?language_code=${encodeURIComponent(languageCode)}`)
        .catch((error) => {
          glossaryRequests.delete(key)
          throw error
        }),
    )
  }
  return glossaryRequests.get(key)
}

export function glossaryConceptFragment(conceptId) {
  return `#glossary-concept-${encodeURIComponent(conceptId)}`
}
