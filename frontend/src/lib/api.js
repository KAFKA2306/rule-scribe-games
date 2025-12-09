export const api = {
  get: async (path) => {
    const res = await fetch(path)
    if (!res.ok) throw new Error(`API Error: ${res.status}`)
    return res.json()
  },
  post: async (path, body) => {
    const res = await fetch(path, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })
    if (res.status === 429) throw new Error('RATE_LIMIT')
    if (!res.ok) {
      const err = await res.json().catch(() => ({}))
      throw new Error(err.detail || `API Error: ${res.status}`)
    }
    return res.json()
  },
}
