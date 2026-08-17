import { test, expect } from '@playwright/test'

const game = {
  id: 269,
  slug: 'skull-king',
  title: 'Skull King',
  title_ja: 'スカルキング',
  summary: 'トリックテイキングゲーム。',
  rules_content: '# Skull King Rules\n\nルール本文',
  structured_data: {},
}

async function mockGame(page) {
  await page.route('**/api/games**', async route => {
    const url = new URL(route.request().url())
    if (url.pathname === '/api/games/skull-king') {
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ game }) })
      return
    }
    await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ games: [] }) })
  })
}

test('uses the system share sheet when Web Share is available', async ({ page }) => {
  await page.addInitScript(() => {
    window.__shared = null
    Object.defineProperty(navigator, 'share', {
      configurable: true,
      value: async data => { window.__shared = data },
    })
  })
  await mockGame(page)
  await page.goto('/games/skull-king')

  await page.getByRole('button', { name: '共有', exact: true }).click()

  expect(await page.evaluate(() => window.__shared)).toEqual({
    url: 'https://bodoge-no-mikata.vercel.app/games/skull-king',
  })
  await expect(page.getByRole('button', { name: '共有しました' })).toBeVisible()
})

test('falls back to copying the canonical URL when Web Share is unavailable', async ({ page }) => {
  await page.addInitScript(() => {
    window.__copied = null
    Object.defineProperty(navigator, 'share', { configurable: true, value: undefined })
    Object.defineProperty(navigator, 'clipboard', {
      configurable: true,
      value: { writeText: async text => { window.__copied = text } },
    })
  })
  await mockGame(page)
  await page.goto('/games/skull-king')

  await page.getByRole('button', { name: 'リンクをコピー' }).click()

  expect(await page.evaluate(() => window.__copied)).toBe(
    'https://bodoge-no-mikata.vercel.app/games/skull-king',
  )
  await expect(page.getByRole('button', { name: 'コピーしました' })).toBeVisible()
})
