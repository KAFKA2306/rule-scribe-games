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

test('catalogue uses generated WebP when image_url is missing', async ({ page }) => {
  await page.route('**/api/games?**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        games: [
          {
            id: 'missing-image-fixture',
            slug: 'bounce-off',
            title: 'Bounce-Off',
            title_ja: 'バウンス・オフ！',
            image_url: null,
            min_players: 2,
            max_players: 4,
            play_time: 15,
            published_year: 2014,
          },
        ],
        total: 1,
      }),
    })
  })

  await page.goto('/')

  const image = page.getByRole('img', { name: 'バウンス・オフ！' })
  await expect(image).toHaveAttribute('src', '/images/games/generated/bounce-off.webp')
})
