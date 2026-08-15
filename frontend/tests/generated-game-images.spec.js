import { test, expect } from '@playwright/test'

const generatedImages = [
  'bounce-off',
  'font-karuta',
  'bob-jiten',
  'bob-jiten-kids',
  'we-didnt-playtest-this-at-all',
]

test('games that were missing artwork are generated as WebP assets', async ({ request }) => {
  for (const slug of generatedImages) {
    const response = await request.get(`/images/games/generated/${slug}.webp`)
    expect(response.ok(), slug).toBeTruthy()
    expect(response.headers()['content-type'], slug).toContain('image/webp')

    const body = await response.body()
    expect(body.subarray(0, 4).toString('ascii'), slug).toBe('RIFF')
    expect(body.subarray(8, 12).toString('ascii'), slug).toBe('WEBP')
  }
})
