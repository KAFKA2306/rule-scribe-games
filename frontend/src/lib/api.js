const handleResponse = async (res) => {
  if (!res.ok) {
    const errorBody = await res.json().catch(() => ({}))
    throw new Error(errorBody.message || `API Error: ${res.status} ${res.statusText}`)
  }
  return res.json()
}

export const api = {
  get: async (path) => {
    const res = await fetch(path)
    return handleResponse(res)
  },
  post: async (path, body) => {
    const res = await fetch(path, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })
    return handleResponse(res)
  },
  patch: async (path, body) => {
    const res = await fetch(path, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })
    return handleResponse(res)
  },
}
