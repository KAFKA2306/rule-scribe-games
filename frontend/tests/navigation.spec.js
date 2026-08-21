import { test, expect } from '@playwright/test'

const USER_ID = 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa'
const LIST_ID = 'aaaaaaaa-0000-4000-8000-000000000001'
const GAME_ID = '11111111-1111-4111-8111-111111111111'
const TOKEN = 'eyJhbGciOiJub25lIn0.eyJzdWIiOiJhYWFhYWFhYS1hYWFhLTRhYWEtOGFhYS1hYWFhYWFhYWFhYWFhYSIsInJvbGUiOiJhdXRoZW50aWNhdGVkIiwiZXhwIjo0MTAyNDQ0ODAwfQ.'

function normalize(value) {
  return (value || '').normalize('NFKC').toLowerCase().trim()
}

function directoryResponse(games, requestUrl) {
  const url = new URL(requestUrl)
  const query = normalize(url.searchParams.get('q'))
  const players = url.searchParams.get('players')
  const time = url.searchParams.get('time')
  const tier = url.searchParams.get('tier')
  const sort = url.searchParams.get('sort') || 'recent'
  const limit = Number.parseInt(url.searchParams.get('limit') || '48', 10)
  const offset = Number.parseInt(url.searchParams.get('offset') || '0', 10)

  let result = [...games]
  if (query) {
    result = result.filter((game) => [game.title, game.title_ja, game.title_en, game.summary, game.description]
      .some((value) => normalize(value).includes(query)))
  }
  if (players) {
    result = result.filter((game) => {
      if (!Number.isFinite(game.min_players) || !Number.isFinite(game.max_players)) return false
      if (players === '5+') return game.max_players >= 5
      const count = Number.parseInt(players, 10)
      return game.min_players <= count && count <= game.max_players
    })
  }
  if (time) {
    result = result.filter((game) => {
      if (!Number.isFinite(game.play_time) || game.play_time <= 0) return false
      if (time === '30-') return game.play_time <= 30
      if (time === '30-60') return game.play_time > 30 && game.play_time <= 60
      if (time === '60-120') return game.play_time > 60 && game.play_time <= 120
      return game.play_time > 120
    })
  }
  if (tier) result = result.filter((game) => game.strategy_tier === tier)

  result.sort((a, b) => {
    if (sort === 'title') return (a.title_ja || a.title || '').localeCompare(b.title_ja || b.title || '')
    if (sort === 'year') return (b.published_year || 0) - (a.published_year || 0)
    if (sort === 'play_time') {
      const aTime = Number.isFinite(a.play_time) && a.play_time > 0 ? a.play_time : Number.POSITIVE_INFINITY
      const bTime = Number.isFinite(b.play_time) && b.play_time > 0 ? b.play_time : Number.POSITIVE_INFINITY
      return aTime - bTime
    }
    return (b.created_at ? new Date(b.created_at).getTime() : 0) - (a.created_at ? new Date(a.created_at).getTime() : 0)
  })

  return {
    games: result.slice(offset, offset + limit),
    total: result.length,
    limit,
    offset,
  }
}

async function mockDirectory(page, games, { failFirst = false } = {}) {
  let requests = 0
  await page.route('**/api/games?*', async (route) => {
    requests += 1
    if (failFirst && requests === 1) {
      await route.fulfill({ status: 503, contentType: 'application/json', body: JSON.stringify({ detail: 'unavailable' }) })
      return
    }
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(directoryResponse(games, route.request().url())),
    })
  })
  return () => requests
}

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
  await mockDirectory(page, [
    { id: GAME_ID, slug: 'game-one', title: 'Game One', title_ja: 'ゲーム1', summary: 'summary', min_players: 2, max_players: 4 },
  ])
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
  await mockDirectory(page, games)

  await page.goto('/')
  await page.getByLabel('ゲームの並び順').selectOption('play_time')

  await expect(page.locator('.asset-title')).toHaveText(['30分ゲーム', '45分ゲーム', '時間未確認ゲーム'])
})

test('player filters exclude games with unknown player bounds', async ({ page }) => {
  const games = [
    { id: '1', slug: 'known', title_ja: '2人対応ゲーム', min_players: 2, max_players: 4, play_time: 30 },
    { id: '2', slug: 'unknown', title_ja: '人数未確認ゲーム', min_players: null, max_players: null, play_time: null },
  ]
  await mockDirectory(page, games)

  await page.goto('/')
  await page.getByRole('button', { name: '2人', exact: true }).click()

  await expect(page.locator('.asset-title')).toHaveText(['2人対応ゲーム'])
  await expect(page.getByText('人数未確認ゲーム', { exact: true })).toHaveCount(0)
})

test('play-time filter chip uses the visible label instead of the internal filter id', async ({ page }) => {
  const games = [
    { id: '1', slug: 'short', title_ja: '30分ゲーム', min_players: 2, max_players: 4, play_time: 30 },
    { id: '2', slug: 'medium', title_ja: '45分ゲーム', min_players: 2, max_players: 4, play_time: 45 },
  ]
  await mockDirectory(page, games)

  await page.goto('/')
  await page.getByRole('button', { name: '30分以内', exact: true }).click()

  await expect(page.locator('.filter-chip').filter({ hasText: '時間:' })).toContainText('時間: 30分以内')
  await expect(page.getByText('時間: 30-', { exact: true })).toHaveCount(0)
})

test('comparison renders missing player count and duration as unknown', async ({ page }) => {
  const games = [
    { id: '1', slug: 'known', title_ja: '既知ゲーム', min_players: 2, max_players: 4, play_time: 30 },
    { id: '2', slug: 'unknown', title_ja: '未確認ゲーム', min_players: null, max_players: null, play_time: null },
  ]
  await mockDirectory(page, games)

  await page.goto('/')
  await page.getByRole('button', { name: '既知ゲームを比較に追加' }).click()
  await page.getByRole('button', { name: '未確認ゲームを比較に追加' }).click()
  await page.getByRole('button', { name: '比較する' }).click()

  const known = page.locator('.battle-col').filter({ hasText: '既知ゲーム' })
  const unknown = page.locator('.battle-col').filter({ hasText: '未確認ゲーム' })
  await expect(known.getByText('2-4人', { exact: true })).toBeVisible()
  await expect(known.getByText('30分', { exact: true })).toBeVisible()
  await expect(unknown.getByText('不明', { exact: true })).toHaveCount(2)
  await expect(page.getByText('null分', { exact: true })).toHaveCount(0)
  await expect(page.getByText('null-null', { exact: true })).toHaveCount(0)
})

test('directory prioritizes only the first visible game image', async ({ page }) => {
  const games = [
    { id: '1', slug: 'first', title_ja: '最初のゲーム', image_url: '/first.webp' },
    { id: '2', slug: 'second', title_ja: '次のゲーム', image_url: '/second.webp' },
  ]
  await mockDirectory(page, games)

  await page.goto('/')

  const images = page.locator('.asset-thumb')
  await expect(images).toHaveCount(2)
  await expect(images.nth(0)).toHaveAttribute('loading', 'eager')
  await expect(images.nth(0)).toHaveAttribute('fetchpriority', 'high')
  await expect(images.nth(1)).toHaveAttribute('loading', 'lazy')
  await expect(images.nth(1)).toHaveAttribute('fetchpriority', 'auto')
})

test('directory labels unverified and review-required games without warning reviewed games', async ({ page }) => {
  const games = [
    { id: '1', slug: 'unverified', title_ja: '未検証ゲーム', identity_status: 'unverified', content_review_status: 'unknown' },
    { id: '2', slug: 'review', title_ja: '要確認ゲーム', identity_status: 'verified', content_review_status: 'review_required' },
    { id: '3', slug: 'reviewed', title_ja: '確認済みゲーム', identity_status: 'verified', content_review_status: 'human_reviewed' },
  ]
  await mockDirectory(page, games)

  await page.goto('/')

  const unverified = page.locator('.asset-card-shell').filter({ hasText: '未検証ゲーム' })
  const review = page.locator('.asset-card-shell').filter({ hasText: '要確認ゲーム' })
  const reviewed = page.locator('.asset-card-shell').filter({ hasText: '確認済みゲーム' })
  await expect(unverified.getByText('未検証', { exact: true })).toBeVisible()
  await expect(review.getByText('内容要確認', { exact: true })).toBeVisible()
  await expect(reviewed.getByText('未検証', { exact: true })).toHaveCount(0)
  await expect(reviewed.getByText('内容要確認', { exact: true })).toHaveCount(0)

  await page.getByRole('button', { name: '未検証ゲームを比較に追加' }).click()
  await page.getByRole('button', { name: '要確認ゲームを比較に追加' }).click()
  await page.getByRole('button', { name: '確認済みゲームを比較に追加' }).click()
  await page.getByRole('button', { name: '比較する' }).click()

  const comparedUnverified = page.locator('.battle-col').filter({ hasText: '未検証ゲーム' })
  const comparedReview = page.locator('.battle-col').filter({ hasText: '要確認ゲーム' })
  const comparedReviewed = page.locator('.battle-col').filter({ hasText: '確認済みゲーム' })
  await expect(comparedUnverified.getByText('未検証', { exact: true })).toBeVisible()
  await expect(comparedReview.getByText('内容要確認', { exact: true })).toBeVisible()
  await expect(comparedReviewed.getByText('未検証', { exact: true })).toHaveCount(0)
  await expect(comparedReviewed.getByText('内容要確認', { exact: true })).toHaveCount(0)
})

test('directory load failure stays distinct from empty results and can be retried', async ({ page }) => {
  const games = [{ id: '1', slug: 'retry-game', title_ja: '再読込ゲーム' }]
  const requestCount = await mockDirectory(page, games, { failFirst: true })

  await page.goto('/')

  await expect(page.getByRole('alert')).toContainText('ゲームの読み込みに失敗しました。')
  await expect(page.getByText('条件に一致するゲームが見つかりません。', { exact: true })).toHaveCount(0)
  await page.getByRole('button', { name: '再読み込み' }).click()

  await expect(page.getByRole('alert')).toHaveCount(0)
  await expect(page.getByText('再読込ゲーム', { exact: true })).toBeVisible()
  expect(requestCount()).toBe(2)
})
