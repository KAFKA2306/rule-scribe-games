import { test, expect } from '@playwright/test'

const USER_ID = 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa'
const LIST_ID = 'aaaaaaaa-0000-4000-8000-000000000001'
const GAME_ID = '11111111-1111-4111-8111-111111111111'
const TOKEN = 'eyJhbGciOiJub25lIn0.eyJzdWIiOiJhYWFhYWFhYS1hYWFhLTRhYWEtOGFhYS1hYWFhYWFhYWFhYWFhYSIsInJvbGUiOiJhdXRoZW50aWNhdGVkIiwiZXhwIjo0MTAyNDQ0ODAwfQ.'

const delay = (ms) => new Promise((resolve) => setTimeout(resolve, ms))

async function installSession(page) {
  await page.addInitScript(({ token, userId }) => {
    localStorage.setItem('sb-example-auth-token', JSON.stringify({
      access_token: token,
      token_type: 'bearer',
      expires_in: 3600,
      expires_at: 4102444800,
      refresh_token: 'test-refresh',
      user: {
        id: userId,
        aud: 'authenticated',
        role: 'authenticated',
        email: 'user@example.com',
        user_metadata: { full_name: 'Test User' },
      },
    }))
  }, { token: TOKEN, userId: USER_ID })
}

test('game detail coalesces duplicate GET and gives mutation feedback within one frame', async ({ page }) => {
  await installSession(page)
  let gameRequests = 0
  let saveRequests = 0

  await page.route('**/api/games/game-one', async (route) => {
    gameRequests += 1
    await delay(250)
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ id: GAME_ID, slug: 'game-one', title: 'Game One', title_ja: 'ゲーム1', structured_data: {} }),
    })
  })
  await page.route('**/api/games?limit=50', async (route) => {
    await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ games: [] }) })
  })
  await page.route('**/api/lists', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ lists: [{ id: LIST_ID, name: 'Favorites', visibility: 'private', system_key: null }] }),
    })
  })
  await page.route(`**/api/owned-games/${GAME_ID}`, async (route) => {
    await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ owned: false, item_id: null }) })
  })
  await page.route(`**/api/lists/${LIST_ID}/items`, async (route) => {
    saveRequests += 1
    await delay(300)
    await route.fulfill({ status: 201, contentType: 'application/json', body: JSON.stringify({ id: 'item-1', game_id: GAME_ID }) })
  })

  await page.goto('/games/game-one')
  await expect(page.getByRole('button', { name: 'リストに保存' })).toBeVisible()
  expect(gameRequests).toBe(1)

  const feedback = await page.evaluate(() => new Promise((resolve) => {
    const button = [...document.querySelectorAll('button')].find((candidate) => candidate.textContent.includes('リストに保存'))
    const start = performance.now()
    button.click()
    button.click()
    requestAnimationFrame(() => resolve({ elapsedMs: performance.now() - start, text: button.textContent }))
  }))
  expect(feedback.elapsedMs).toBeLessThan(100)
  expect(feedback.text).toContain('保存中')
  await expect(page.getByText('保存しました', { exact: true })).toBeVisible()
  expect(saveRequests).toBe(1)
})

test('lists bootstrap index/detail in parallel and list switching does not refetch the index', async ({ page }) => {
  await installSession(page)
  let indexRequests = 0
  let detailRequests = 0
  let indexStartedAt = 0
  let ownedStartedAt = 0

  await page.route('**/api/lists', async (route) => {
    indexRequests += 1
    indexStartedAt = Date.now()
    await delay(250)
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ lists: [{ id: LIST_ID, name: 'Favorites', visibility: 'private', system_key: null }] }),
    })
  })
  await page.route('**/api/owned-games', async (route) => {
    ownedStartedAt = Date.now()
    await delay(250)
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ id: null, name: '所持ゲーム', visibility: 'private', system_key: 'owned', items: [] }),
    })
  })
  await page.route(`**/api/lists/${LIST_ID}`, async (route) => {
    detailRequests += 1
    await delay(150)
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ id: LIST_ID, name: 'Favorites', visibility: 'private', system_key: null, items: [] }),
    })
  })

  await page.goto('/lists')
  await expect(page.getByRole('heading', { name: '所持ゲーム' })).toBeVisible()
  expect(Math.abs(indexStartedAt - ownedStartedAt)).toBeLessThan(100)
  expect(indexRequests).toBe(1)

  await page.getByRole('button', { name: 'Favorites' }).click()
  await expect(page.getByRole('heading', { name: 'Favorites' })).toBeVisible()
  expect(indexRequests).toBe(1)
  expect(detailRequests).toBe(1)
})

test('slow failed list load times out and exposes a retry action instead of waiting forever', async ({ page }) => {
  await installSession(page)
  await page.route('**/api/lists', async (route) => {
    await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ lists: [] }) })
  })
  await page.route('**/api/owned-games', async (route) => {
    await delay(2000)
    await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ id: null, name: '所持ゲーム', system_key: 'owned', items: [] }) })
  })

  await page.goto('/lists')
  await expect(page.getByRole('alert')).toContainText('タイムアウト', { timeout: 2000 })
  await expect(page.getByRole('button', { name: '再試行' })).toBeVisible()
})

test('auth bootstrap keeps cumulative layout shift below the release threshold', async ({ page }) => {
  await page.addInitScript(() => {
    window.__cls = 0
    new PerformanceObserver((list) => {
      for (const entry of list.getEntries()) {
        if (!entry.hadRecentInput) window.__cls += entry.value
      }
    }).observe({ type: 'layout-shift', buffered: true })
  })

  await page.goto('/lists')
  await expect(page.getByRole('heading', { name: 'マイリスト' })).toBeVisible()
  await page.waitForTimeout(100)
  const cls = await page.evaluate(() => window.__cls || 0)
  expect(cls).toBeLessThan(0.1)
})
