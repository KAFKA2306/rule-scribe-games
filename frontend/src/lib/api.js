import { supabase } from './supabase'

const DEFAULT_TIMEOUT_MS = Number(import.meta.env.VITE_API_TIMEOUT_MS || 15000)
const GET_CACHE_TTL_MS = 2000
const inflightGets = new Map()
const recentGets = new Map()

export class ApiError extends Error {
  constructor(message, { status = 0, code = 'api_error', retryable = false } = {}) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.code = code
    this.retryable = retryable
  }
}

const handleResponse = async (res) => {
  if (!res.ok) {
    const errorBody = await res.json().catch(() => ({}))
    throw new ApiError(
      errorBody.message || errorBody.detail || `API Error: ${res.status} ${res.statusText}`,
      { status: res.status, code: 'http_error', retryable: res.status >= 500 || res.status === 408 || res.status === 429 },
    )
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

const emitTiming = (detail) => {
  if (typeof window === 'undefined') return
  window.dispatchEvent(new CustomEvent('api:timing', { detail }))
}

const request = async (path, options = {}) => {
  const startedAt = performance.now()
  const controller = new AbortController()
  const timeoutMs = options.timeoutMs || DEFAULT_TIMEOUT_MS
  const timeout = window.setTimeout(() => controller.abort('timeout'), timeoutMs)
  const method = options.method || 'GET'

  try {
    const authHeaders = await getAuthHeaders()
    const res = await fetch(path, {
      ...options,
      signal: controller.signal,
      headers: {
        ...authHeaders,
        ...(options.headers || {}),
      },
    })
    const result = await handleResponse(res)
    emitTiming({ path, method, durationMs: performance.now() - startedAt, status: res.status, ok: true, cached: false })
    return result
  } catch (error) {
    const timedOut = controller.signal.aborted
    emitTiming({ path, method, durationMs: performance.now() - startedAt, status: error.status || 0, ok: false, timedOut, cached: false })
    if (timedOut) {
      throw new ApiError('通信がタイムアウトしました。再試行してください。', { code: 'timeout', retryable: true })
    }
    if (error instanceof ApiError) throw error
    throw new ApiError(error.message || '通信に失敗しました。再試行してください。', { code: 'network_error', retryable: true })
  } finally {
    window.clearTimeout(timeout)
  }
}

const clearGetCache = () => recentGets.clear()

const get = (path) => {
  const cached = recentGets.get(path)
  if (cached && cached.expiresAt > performance.now()) {
    emitTiming({ path, method: 'GET', durationMs: 0, status: 200, ok: true, cached: true })
    return Promise.resolve(cached.value)
  }
  if (cached) recentGets.delete(path)

  const existing = inflightGets.get(path)
  if (existing) return existing

  const promise = request(path)
    .then((value) => {
      recentGets.set(path, { value, expiresAt: performance.now() + GET_CACHE_TTL_MS })
      return value
    })
    .finally(() => inflightGets.delete(path))
  inflightGets.set(path, promise)
  return promise
}

const mutate = async (path, options) => {
  const result = await request(path, options)
  clearGetCache()
  return result
}

export const api = {
  get,
  clearGetCache,
  post: async (path, body) =>
    mutate(path, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    }),
  put: async (path, body) =>
    mutate(path, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    }),
  patch: async (path, body) =>
    mutate(path, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    }),
  delete: async (path) => mutate(path, { method: 'DELETE' }),
}
