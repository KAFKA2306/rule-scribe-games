import { test, expect } from '@playwright/test'

const USER_ID = 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa'
const LIST_ID = 'aaaaaaaa-0000-4000-8000-000000000001'
const OWNED_LIST_ID = 'aaaaaaaa-0000-4000-8000-000000000002'
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

async function mockGame(page) {
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
}

test('anonymous list route is mobile-usable and offers Google login instead of private mutations', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 })
  await page.goto('/lists')
  await expect(page.getByRole('heading', { name: 'マイリスト' })).toBeVisible()
  await expect(page.getByRole('button', { name: 'Googleでログイン' })).toBeVisible()
  await expect(page.getByRole('button', { name: 'リストを作成' })).toHaveCount(0)
})

test('authenticated list page keeps custom lists separate from the owned system collection', async ({ page }) => {
  await installSession(page)
  await page.route('**/api/lists', async (route) => {
    await expect(route.request().headers()['authorization']).toBe(`Bearer ${TOKEN}`)
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ lists: [{ id: LIST_ID, name: 'Favorites', visibility: 'private', system_key: null }] }),
    })
  })
  await page.route('**/api/owned-games', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ id: null, name: '所持ゲーム', visibility: 'private', system_key: 'owned', items: [] }),
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
        system_key: null,
        items: [
          { id: 'aaaaaaaa-1000-4000-8000-000000000001', game_id: GAME_ID, game_title_snapshot: 'ゲーム1', position: 0, unavailable: false, game: { id: GAME_ID, slug: 'game-one', title_ja: 'ゲーム1', title: 'Game One' } },
          { id: 'aaaaaaaa-1000-4000-8000-000000000002', game_id: null, game_title_snapshot: 'Unavailable Game', position: 1, unavailable: true, game: null },
        ],
      }),
    })
  })

  await page.goto('/lists')
  await expect(page.getByRole('button', { name: '所持ゲーム' })).toBeVisible()
  await expect(page.getByText('所持ゲームはまだありません。')).toBeVisible()
  await page.getByRole('button', { name: 'Favorites' }).click()
  await expect(page.getByText('ゲーム1', { exact: true })).toBeVisible()
  await expect(page.getByText('Unavailable Game', { exact: true })).toBeVisible()
  await expect(page.getByText('現在利用できないゲーム')).toBeVisible()
  await expect(page.getByRole('button', { name: 'ゲーム1を下へ' })).toBeVisible()
})

test('owned collection is mobile-usable and can remove an owned canonical game', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 })
  await installSession(page)
  await page.route('**/api/lists', async (route) => {
    await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ lists: [] }) })
  })
  let removed = false
  await page.route('**/api/owned-games', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        id: OWNED_LIST_ID,
        name: '所持ゲーム',
        visibility: 'private',
        system_key: 'owned',
        items: removed ? [] : [{
          id: 'aaaaaaaa-1000-4000-8000-000000000003',
          game_id: GAME_ID,
          game_title_snapshot: 'ゲーム1',
          position: 0,
          created_at: '2026-08-14T01:34:48Z',
          unavailable: false,
          game: { id: GAME_ID, slug: 'game-one', title_ja: 'ゲーム1', title: 'Game One' },
        }],
      }),
    })
  })
  await page.route(`**/api/owned-games/${GAME_ID}`, async (route) => {
    expect(route.request().method()).toBe('DELETE')
    expect(route.request().headers()['authorization']).toBe(`Bearer ${TOKEN}`)
    removed = true
    await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ owned: false, removed: true }) })
  })

  await page.goto('/lists')
  await expect(page.getByText('ゲーム1', { exact: true })).toBeVisible()
  await page.getByRole('button', { name: '所持解除' }).click()
  await expect(page.getByText('所持ゲームはまだありません。')).toBeVisible()
  expect(removed).toBe(true)
})

test('game detail saves canonical game id to selected custom list with bearer token', async ({ page }) => {
  await installSession(page)
  await mockGame(page)
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
  await expect(page.getByRole('status', { name: '保存しました' })).toBeVisible()
  expect(saved).toBe(true)
})

test('game detail toggles owned state with idempotent canonical-game endpoints', async ({ page }) => {
  await installSession(page)
  await mockGame(page)
  await page.route('**/api/lists', async (route) => {
    await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ lists: [] }) })
  })

  let owned = false
  let putCount = 0
  let deleteCount = 0
  await page.route(`**/api/owned-games/${GAME_ID}`, async (route) => {
    expect(route.request().headers()['authorization']).toBe(`Bearer ${TOKEN}`)
    if (route.request().method() === 'GET') {
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ owned, item_id: null }) })
      return
    }
    if (route.request().method() === 'PUT') {
      putCount += 1
      owned = true
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ owned: true, created: true }) })
      return
    }
    if (route.request().method() === 'DELETE') {
      deleteCount += 1
      owned = false
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ owned: false, removed: true }) })
      return
    }
    await route.abort()
  })

  await page.goto('/games/game-one')
  const toggle = page.getByRole('button', { name: '所持している' })
  await expect(toggle).toBeVisible()
  await toggle.click()
  await expect(page.getByRole('button', { name: '✓ 所持しています' })).toBeVisible()
  await page.getByRole('button', { name: '✓ 所持しています' }).click()
  await expect(page.getByRole('button', { name: '所持している' })).toBeVisible()
  expect(putCount).toBe(1)
  expect(deleteCount).toBe(1)
})
