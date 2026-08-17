import { devices, expect, test } from '@playwright/test'

const relativeSpace = {
  id: 9999,
  slug: 'relative-space',
  title: 'Relative Space',
  title_ja: 'Relative Space',
  min_players: 2,
  max_players: 4,
  play_time: 30,
  min_age: 8,
  published_year: 2026,
  summary: 'Mobile scroll regression fixture.',
  description: 'Mobile scroll regression fixture.',
  rules_content: Array.from(
    { length: 60 },
    (_, index) => `## Section ${index + 1}\n\nScrollable rule text for the mobile regression test.`,
  ).join('\n\n'),
  structured_data: {},
}

async function mockGameApi(page) {
  await page.route('**/api/games**', async route => {
    const url = new URL(route.request().url())
    if (url.pathname === '/api/games/relative-space') {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ game: relativeSpace }),
      })
      return
    }

    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ games: [] }),
    })
  })
}

test('game detail uses document scrolling on a touch viewport', async ({ browser }, testInfo) => {
  test.skip(testInfo.project.name !== 'chromium', 'Run once with an explicit mobile touch context.')

  const context = await browser.newContext({ ...devices['Pixel 5'] })
  const page = await context.newPage()

  try {
    await mockGameApi(page)
    await page.goto('/games/relative-space')
    await expect(page.getByRole('heading', { name: 'Relative Space' })).toBeVisible()

    const state = await page.evaluate(() => {
      const detail = document.querySelector('.game-detail-content')
      if (!detail) throw new Error('game detail container is missing')

      return {
        bodyOverflowY: getComputedStyle(document.body).overflowY,
        detailOverflowY: getComputedStyle(detail).overflowY,
        viewportHeight: window.innerHeight,
        pageHeight: document.documentElement.scrollHeight,
      }
    })

    expect(state.bodyOverflowY).toBe('auto')
    expect(state.detailOverflowY).toBe('visible')
    expect(state.pageHeight).toBeGreaterThan(state.viewportHeight)

    const client = await context.newCDPSession(page)
    await client.send('Input.synthesizeScrollGesture', {
      x: 195,
      y: 650,
      yDistance: -600,
      speed: 800,
      gestureSourceType: 'touch',
    })

    await expect.poll(() => page.evaluate(() => window.scrollY)).toBeGreaterThan(0)
  } finally {
    await context.close()
  }
})
