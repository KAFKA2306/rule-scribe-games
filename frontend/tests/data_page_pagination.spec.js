import { test, expect } from '@playwright/test'

const fixtureGames = [
  { slug: 'first-game', title_ja: '最初のゲーム', min_players: 2, max_players: 4, play_time: 30 },
  { slug: 'second-game', title_ja: '次のゲーム', min_players: 2, max_players: 4, play_time: 60 },
  { slug: 'third-game', title_ja: '最後のゲーム', min_players: 3, max_players: 5, play_time: 45 },
]

test('/data requests at most 100 games per request and aggregates every page', async ({ page }) => {
  const requests = []
  let overLimitRequest = false

  await page.route('**/api/games?*', async (route) => {
    const url = new URL(route.request().url())
    const limit = Number(url.searchParams.get('limit'))
    const offset = Number(url.searchParams.get('offset'))
    requests.push({ limit, offset })

    if (limit > 100) {
      overLimitRequest = true
      await route.fulfill({
        status: 422,
        contentType: 'application/json',
        body: '{"detail":"limit too large"}',
      })
      return
    }

    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        games: fixtureGames.slice(offset, offset + 2),
        total: fixtureGames.length,
        limit,
        offset,
      }),
    })
  })

  await page.goto('/data')

  await expect(page.locator('.stat-card').first().locator('p')).toHaveText('3')
  await expect(page.getByRole('link', { name: '最初のゲーム' })).toBeVisible()
  expect(requests).toEqual([
    { limit: 100, offset: 0 },
    { limit: 100, offset: 2 },
  ])
  expect(overLimitRequest).toBe(false)
})
