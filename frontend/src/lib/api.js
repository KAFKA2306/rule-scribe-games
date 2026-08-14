import { supabase } from './supabase'

const handleResponse = async (res) => {
  if (!res.ok) {
    const errorBody = await res.json().catch(() => ({}))
    throw new Error(errorBody.message || errorBody.detail || `API Error: ${res.status} ${res.statusText}`)
  }
  if (res.status === 204) return null
  return res.json()
}

const getAuthHeaders = async () => {
  if (!supabase) return {}
  const { data } = await supabase.auth.getSession()
  const accessToken = data.session?.access_token
  return accessToken ? { Authorization: `Bearer ${accessToken}` } : {}
}

const request = async (path, options = {}) => {
  const authHeaders = await getAuthHeaders()
  const res = await fetch(path, {
    ...options,
    headers: {
      ...authHeaders,
      ...(options.headers || {}),
    },
  })
  return handleResponse(res)
}

export const api = {
  get: async (path) => request(path),
  post: async (path, body) =>
    request(path, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    }),
  put: async (path, body) =>
    request(path, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    }),
  patch: async (path, body) =>
    request(path, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    }),
  delete: async (path) => request(path, { method: 'DELETE' }),
}
