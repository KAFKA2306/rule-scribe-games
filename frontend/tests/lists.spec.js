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

test('anonymous list route is mobile-usable and offers Google login instead of private mutations', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 })
  await page.goto('/lists')
  await expect(page.getByRole('heading', { name: 'マイリスト' })).toBeVisible()
  await expect(page.getByRole('button', { name: 'Googleでログイン' })).toBeVisible()
  await expect(page.getByRole('button', { name: 'リストを作成' })).toHaveCount(0)
})

test('authenticated list page renders private list and reorder/remove controls', async ({ page }) => {
  await installSession(page)
  await page.route('**/api/lists', async (route) => {
    await expect(route.request().headers()['authorization']).toBe(`Bearer ${TOKEN}`)
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ lists: [{ id: LIST_ID, name: 'Favorites', visibility: 'private' }] }),
    })
  })
  await page.route(`**/api/lists/${LIST_ID}`, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        id: LIST_ID,
        name: 'Favorites',
        visibility: 'private',
        items: [
          { id: 'aaaaaaaa-1000-4000-8000-000000000001', game_id: GAME_ID, game_title_snapshot: 'ゲーム1', position: 0, unavailable: false, game: { id: GAME_ID, slug: 'game-one', title_ja: 'ゲーム1', title: 'Game One' } },
          { id: 'aaaaaaaa-1000-4000-8000-000000000002', game_id: null, game_title_snapshot: 'Unavailable Game', position: 1, unavailable: true, game: null },
        ],
      }),
    })
  })

  await page.goto('/lists')
  await expect(page.getByText('Favorites', { exact: true }).first()).toBeVisible()
  await expect(page.getByText('ゲーム1', { exact: true })).toBeVisible()
  await expect(page.getByText('Unavailable Game', { exact: true })).toBeVisible()
  await expect(page.getByText('現在利用できないゲーム')).toBeVisible()
  await expect(page.getByRole('button', { name: 'ゲーム1を下へ' })).toBeVisible()
})

test('game detail saves canonical game id to selected user list with bearer token', async ({ page }) => {
  await installSession(page)
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
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ lists: [{ id: LIST_ID, name: 'Favorites', visibility: 'private' }] }),
    })
  })

  let saved = false
  await page.route(`**/api/lists/${LIST_ID}/items`, async (route) => {
    expect(route.request().method()).toBe('POST')
    expect(route.request().headers()['authorization']).toBe(`Bearer ${TOKEN}`)
    expect(route.request().postDataJSON()).toEqual({ game_id: GAME_ID })
    saved = true
    await route.fulfill({
      status: 201,
      contentType: 'application/json',
      body: JSON.stringify({ id: 'item-1', game_id: GAME_ID }),
    })
  })

  await page.goto('/games/game-one')
  await expect(page.getByRole('button', { name: 'リストに保存' })).toBeVisible()
  await page.getByRole('button', { name: 'リストに保存' }).click()
  await expect(page.getByRole('status')).toContainText('保存しました')
  expect(saved).toBe(true)
})
