import { test, expect } from '@playwright/test'

const USER_ID = 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa'
const LIST_ID = 'aaaaaaaa-0000-4000-8000-000000000001'
const GAME_ID = '11111111-1111-4111-8111-111111111111'
const TOKEN = 'eyJhbGciOiJub25lIn0.eyJzdWIiOiJhYWFhYWFhYS1hYWFhLTRhYWEtOGFhYS1hYWFhYWFhYWFhYWFhYSIsInJvbGUiOiJhdXRoZW50aWNhdGVkIiwiZXhwIjo0MTAyNDQ0ODAwfQ.'

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

async function mockNavigationApis(page) {
  await page.route('**/api/games?limit=20000&offset=0', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        games: [{ id: GAME_ID, slug: 'game-one', title: 'Game One', title_ja: 'ゲーム1', summary: 'summary', min_players: 2, max_players: 4 }],
        total: 1,
      }),
    })
  })
  await page.route('**/api/games/game-one', async (route) => {
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
    await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ lists: [] }) })
  })
  await page.route(`**/api/owned-games/${GAME_ID}`, async (route) => {
    await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ owned: false, item_id: null }) })
  })
  await page.route('**/api/owned-games', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ id: null, name: '所持ゲーム', visibility: 'private', system_key: 'owned', items: [] }),
    })
  })
}

test('directory -> game -> lists stays in one document and browser back restores query context', async ({ page }) => {
  await installSession(page)
  await mockNavigationApis(page)
  await page.goto('/?q=ゲーム')
  await expect(page.getByText('ゲーム1', { exact: true }).first()).toBeVisible()

  await page.evaluate(() => { window.__spaContinuityMarker = 'alive' })
  const gameLink = page.getByRole('link', { name: /ゲーム1/ }).first()
  await gameLink.click()
  await expect(page.locator('[data-navigation-feedback]')).toBeVisible()
  await expect(page).toHaveURL(/\/games\/game-one$/)
  await expect.poll(() => page.evaluate(() => document.activeElement?.matches('main, .game-detail-content'))).toBe(true)
  expect(await page.evaluate(() => window.__spaContinuityMarker)).toBe('alive')
  expect(await page.evaluate(() => performance.getEntriesByType('navigation').length)).toBe(1)

  await expect(page.getByRole('link', { name: 'リストを作成' })).toBeVisible()
  await page.getByRole('link', { name: 'リストを作成' }).click()
  await expect(page.locator('[data-navigation-feedback]')).toBeVisible()
  await expect(page).toHaveURL(/\/lists$/)
  expect(await page.evaluate(() => window.__spaContinuityMarker)).toBe('alive')
  expect(await page.evaluate(() => performance.getEntriesByType('navigation').length)).toBe(1)

  await page.goBack()
  await expect(page).toHaveURL(/\/games\/game-one$/)
  await page.goBack()
  await expect(page).toHaveURL(/\/?\?q=(?:%E3%82%B2%E3%83%BC%E3%83%A0|ゲーム)$/)
  await expect(page.getByText('ゲーム1', { exact: true }).first()).toBeVisible()
  expect(await page.evaluate(() => window.__spaContinuityMarker)).toBe('alive')
})

test('selected list is encoded in history so back and forward restore list context', async ({ page }) => {
  await installSession(page)
  await page.route('**/api/lists', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ lists: [{ id: LIST_ID, name: 'Favorites', visibility: 'private', system_key: null }] }),
    })
  })
  await page.route(`**/api/lists/${LIST_ID}`, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ id: LIST_ID, name: 'Favorites', visibility: 'private', system_key: null, items: [] }),
    })
  })
  await page.route('**/api/owned-games', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ id: null, name: '所持ゲーム', visibility: 'private', system_key: 'owned', items: [] }),
    })
  })

  await page.goto(`/lists?list=${LIST_ID}&notice=saved`)
  await expect(page.getByRole('heading', { name: 'Favorites' })).toBeVisible()
  await expect(page.getByRole('status')).toContainText('保存したリストを表示しています')

  await page.getByRole('button', { name: '所持ゲーム' }).click()
  await expect(page).toHaveURL(/\/lists$/)
  await expect(page.getByRole('heading', { name: '所持ゲーム' })).toBeVisible()

  await page.goBack()
  await expect(page).toHaveURL(new RegExp(`/lists\\?list=${LIST_ID}`))
  await expect(page.getByRole('heading', { name: 'Favorites' })).toBeVisible()

  await page.goForward()
  await expect(page).toHaveURL(/\/lists$/)
  await expect(page.getByRole('heading', { name: '所持ゲーム' })).toBeVisible()
})

test('mobile filter drawer moves, contains, and restores keyboard focus', async ({ page }) => {
  await page.setViewportSize({ width: 375, height: 812 })
  await mockNavigationApis(page)
  await page.goto('/')

  const toggle = page.getByRole('button', { name: 'フィルター', exact: true })
  await toggle.click()

  const dialog = page.getByRole('dialog', { name: 'ゲーム絞り込み' })
  const close = dialog.getByRole('button', { name: 'フィルターを閉じる' })
  const reset = dialog.getByRole('button', { name: 'フィルターをリセット' })

  await expect(dialog).toBeVisible()
  await expect(close).toBeFocused()

  await page.keyboard.press('Shift+Tab')
  await expect(reset).toBeFocused()
  await page.keyboard.press('Tab')
  await expect(close).toBeFocused()

  await page.keyboard.press('Escape')
  await expect(toggle).toBeFocused()
  await expect(page.locator('#directory-filters')).not.toHaveClass(/mobile-open/)
})

test('homepage links to a JSON Web App Manifest', async ({ page, request }) => {
  await page.goto('/')

  await expect(page.locator('link[rel="manifest"]')).toHaveAttribute('href', '/manifest.webmanifest')

  const response = await request.get('/manifest.webmanifest')
  expect(response.ok()).toBeTruthy()
  expect(response.headers()['content-type']).toContain('application/manifest+json')

  const manifest = await response.json()
  expect(manifest).toMatchObject({
    id: '/',
    name: 'ボドゲのミカタ',
    short_name: 'ボドゲのミカタ',
    lang: 'ja',
    start_url: '/',
    scope: '/',
    display: 'standalone',
  })
})

test('play-time sorting keeps unknown durations after known games', async ({ page }) => {
  const games = [
    { id: '1', slug: 'short', title_ja: '30分ゲーム', min_players: 2, max_players: 4, play_time: 30 },
    { id: '2', slug: 'medium', title_ja: '45分ゲーム', min_players: 2, max_players: 4, play_time: 45 },
    { id: '3', slug: 'unknown', title_ja: '時間未確認ゲーム', min_players: 2, max_players: 4, play_time: null },
  ]
  await page.route('**/api/games?limit=20000&offset=0', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ games, total: games.length }),
    })
  })

  await page.goto('/')
  await page.getByLabel('ゲームの並び順').selectOption('play_time')

  await expect(page.locator('.asset-title')).toHaveText(['30分ゲーム', '45分ゲーム', '時間未確認ゲーム'])
})

test('directory prioritizes only the first visible game image', async ({ page }) => {
  const games = [
    { id: '1', slug: 'first', title_ja: '最初のゲーム', image_url: '/first.webp' },
    { id: '2', slug: 'second', title_ja: '次のゲーム', image_url: '/second.webp' },
  ]
  await page.route('**/api/games?limit=20000&offset=0', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ games, total: games.length }),
    })
  })

  await page.goto('/')

  const images = page.locator('.asset-thumb')
  await expect(images).toHaveCount(2)
  await expect(images.nth(0)).toHaveAttribute('loading', 'eager')
  await expect(images.nth(0)).toHaveAttribute('fetchpriority', 'high')
  await expect(images.nth(1)).toHaveAttribute('loading', 'lazy')
  await expect(images.nth(1)).toHaveAttribute('fetchpriority', 'auto')
})
