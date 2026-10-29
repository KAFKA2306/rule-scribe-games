import handler from '../api/ai-search.js'

function createResponse() {
  return {
    statusCode: 200,
    body: null,
    headers: {},
    setHeader(name, value) {
      this.headers[name.toLowerCase()] = value
    },
    status(code) {
      this.statusCode = code
      return this
    },
    json(body) {
      this.body = body
      return this
    },
  }
}

async function gatewayCredits(token) {
  if (!token) return null
  const response = await fetch('https://ai-gateway.vercel.sh/v1/credits', {
    headers: { Authorization: `Bearer ${token}` },
  })
  if (!response.ok) return null
  const data = await response.json()
  return {
    balance: data.balance,
    totalUsed: data.total_used,
  }
}

const token = process.env.VERCEL_OIDC_TOKEN
if (!token) {
  throw new Error('VERCEL_OIDC_TOKEN is required for the Jev gateway smoke test')
}

const before = await gatewayCredits(token)
const request = {
  method: 'POST',
  body: { query: '4人で30〜60分くらいのボードゲーム' },
}
const response = createResponse()

await handler(request, response)

if (response.statusCode !== 200) {
  throw new Error(`Jev endpoint returned ${response.statusCode}: ${JSON.stringify(response.body)}`)
}
if (response.body?.model !== 'typesafe-ai/jev') {
  throw new Error(`Unexpected model: ${JSON.stringify(response.body)}`)
}
if (response.body?.players !== '4') {
  throw new Error(`Expected players=4, got ${JSON.stringify(response.body)}`)
}
if (response.body?.time !== '30-60') {
  throw new Error(`Expected time=30-60, got ${JSON.stringify(response.body)}`)
}

const after = await gatewayCredits(token)
const creditsUnchanged =
  before && after
    ? before.balance === after.balance && before.totalUsed === after.totalUsed
    : null

console.log(
  JSON.stringify({
    ok: true,
    model: response.body.model,
    players: response.body.players,
    time: response.body.time,
    creditsCheck: creditsUnchanged === null ? 'unavailable' : creditsUnchanged ? 'unchanged' : 'changed',
  }),
)
