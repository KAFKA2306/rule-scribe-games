export const api = {
  get: async (path) => {
    const res = await fetch(path)
    return res.json()
  },
  post: async (path, body) => {
    const res = await fetch(path, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })

    return res.json()
  },
}
