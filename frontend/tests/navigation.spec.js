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

  await expect(page).toHaveURL(/\/games\/game-one$/)
  await expect(page.locator('[data-navigation-feedback]')).toBeVisible()
  await expect(page.locator('#route-content')).toBeFocused()
  expect(await page.evaluate(() => window.__spaContinuityMarker)).toBe('alive')
  expect(await page.evaluate(() => performance.getEntriesByType('navigation').length)).toBe(1)

  await expect(page.getByRole('link', { name: 'リストを作成' })).toBeVisible()
  await page.getByRole('link', { name: 'リストを作成' }).click()
  await expect(page).toHaveURL(/\/lists$/)
  expect(await page.evaluate(() => window.__spaContinuityMarker)).toBe('alive')
  expect(await page.evaluate(() => performance.getEntriesByType('navigation').length)).toBe(1)

  await page.goBack()
  await expect(page).toHaveURL(/\/games\/game-one$/)
  await page.goBack()
  await expect(page).toHaveURL(/\/?\?q=%E3%82%B2%E3%83%BC%E3%83%A0$/)
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
