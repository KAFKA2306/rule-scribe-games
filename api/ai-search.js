import { experimental_evaluate as evaluate } from 'ai'

const MAX_QUERY_LENGTH = 300

const PLAYER_VALUES = {
  any: null,
  one: '1',
  two: '2',
  three: '3',
  four: '4',
  five_plus: '5+',
}

const TIME_VALUES = {
  any: null,
  up_to_30: '30-',
  from_30_to_60: '30-60',
  from_60_to_120: '60-120',
  over_120: '120+',
}

function readJsonBody(request) {
  if (request.body && typeof request.body === 'object') return request.body
  if (typeof request.body !== 'string') return null
  try {
    return JSON.parse(request.body)
  } catch {
    return null
  }
}

function resolveChoice(answer, values, questionName) {
  if (!answer || answer.type !== 'choice' || !(answer.choice in values)) {
    throw new Error(`Invalid Jev answer for ${questionName}`)
  }
  return values[answer.choice]
}

function selectedProbability(answer) {
  if (!answer || answer.type !== 'choice' || !answer.probabilities) return null
  const value = answer.probabilities[answer.choice]
  return Number.isFinite(value) ? value : null
}

export default async function handler(request, response) {
  response.setHeader('Cache-Control', 'no-store')

  if (request.method !== 'POST') {
    response.setHeader('Allow', 'POST')
    return response.status(405).json({ error: 'method_not_allowed' })
  }

  const body = readJsonBody(request)
  const query = typeof body?.query === 'string' ? body.query.trim() : ''

  if (!query || query.length > MAX_QUERY_LENGTH) {
    return response.status(400).json({
      error: 'invalid_query',
      message: `query must be 1-${MAX_QUERY_LENGTH} characters`,
    })
  }

  try {
    const result = await evaluate({
      model: 'typesafe-ai/jev',
      state: query,
      questions: {
        players: {
          type: 'choice',
          instructions: 'ボードゲームを探す人が明示したプレイ人数条件を1つ選んでください。人数条件がなければ any。',
          criteria: {
            any: '人数条件が明示されていない',
            one: '1人で遊びたい',
            two: '2人で遊びたい',
            three: '3人で遊びたい',
            four: '4人で遊びたい',
            five_plus: '5人以上で遊びたい',
          },
        },
        play_time: {
          type: 'choice',
          instructions: 'ボードゲームを探す人が明示したプレイ時間帯を1つ選んでください。時間条件がなければ any。',
          criteria: {
            any: 'プレイ時間条件が明示されていない',
            up_to_30: '30分以内',
            from_30_to_60: '30分から60分',
            from_60_to_120: '60分から120分',
            over_120: '120分以上',
          },
        },
      },
      providerOptions: {
        gateway: {
          zeroDataRetention: true,
        },
      },
    })

    const playersAnswer = result.answers.players
    const timeAnswer = result.answers.play_time

    return response.status(200).json({
      model: 'typesafe-ai/jev',
      players: resolveChoice(playersAnswer, PLAYER_VALUES, 'players'),
      time: resolveChoice(timeAnswer, TIME_VALUES, 'play_time'),
      confidence: {
        players: selectedProbability(playersAnswer),
        time: selectedProbability(timeAnswer),
      },
    })
  } catch (error) {
    console.error('Jev evaluation failed', error instanceof Error ? error.message : String(error))
    return response.status(502).json({
      error: 'jev_evaluation_failed',
      message: 'AI条件の判定に失敗しました。',
    })
  }
}
