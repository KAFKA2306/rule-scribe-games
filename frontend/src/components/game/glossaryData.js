import { api } from '../../lib/api'

const glossaryRequests = new Map()

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
