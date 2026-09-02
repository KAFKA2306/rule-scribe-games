import { test, expect } from '@playwright/test'

const games = [
  { id: '11111111-1111-4111-8111-111111111111', slug: 'game-one', title: 'Game One', title_ja: 'ゲーム1', summary: '宇宙のゲーム', min_players: 2, max_players: 4, play_time: 30, published_year: 2026, structured_data: {} },
  { id: '22222222-2222-4222-8222-222222222222', slug: 'game-two', title: 'Game Two', title_ja: 'ゲーム2', summary: '森のゲーム', min_players: 3, max_players: 5, play_time: 45, published_year: 2025, structured_data: {} },
  { id: '33333333-3333-4333-8333-333333333333', slug: 'game-three', title: 'Game Three', title_ja: 'ゲーム3', summary: '海のゲーム', min_players: 2, max_players: 6, play_time: 60, published_year: 2024, structured_data: {} },
  { id: '44444444-4444-4444-8444-444444444444', slug: 'game-four', title: 'Game Four', title_ja: 'ゲーム4', summary: '山のゲーム', min_players: 4, max_players: 8, play_time: 90, published_year: 2023, structured_data: {} },
]

function normalize(value) {
  return (value || '').normalize('NFKC').toLowerCase().trim()
}

function directoryResponse(url) {
  const query = normalize(url.searchParams.get('q'))
  const players = url.searchParams.get('players')
  const limit = Number.parseInt(url.searchParams.get('limit') || '48', 10)
  const offset = Number.parseInt(url.searchParams.get('offset') || '0', 10)

  let result = games.filter((game) => {
    if (query && ![game.title, game.title_ja, game.summary].some((value) => normalize(value).includes(query))) return false
    if (!players) return true
    if (!Number.isFinite(game.min_players) || !Number.isFinite(game.max_players)) return false
    if (players === '5+') return game.max_players >= 5
    const count = Number.parseInt(players, 10)
    return game.min_players <= count && count <= game.max_players
  })

  return {
    games: result.slice(offset, offset + limit),
    total: result.length,
    limit,
    offset,
  }
}

async function mockDirectory(page, counters = { generated: 0 }) {
  await page.route('**/api/**', async (route) => {
    const request = route.request()
    const url = new URL(request.url())
    if (url.pathname === '/api/games' && request.method() === 'GET') {
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(directoryResponse(url)) })
      return
    }
    if (url.pathname === '/api/search' && request.method() === 'POST') {
      counters.generated += 1
      await route.fulfill({ status: 403, contentType: 'application/json', body: JSON.stringify({ detail: 'Catalog generation is not available from public search' }) })
      return
    }
    await route.fulfill({ status: 404, contentType: 'application/json', body: JSON.stringify({ detail: 'not mocked' }) })
  })
}

async function mockGameDetail(page) {
  const detail = {
    ...games[0],
    rules_content: '## 目的\n最初に勝利条件を満たします。',
    setup_summary: 'カードを配ります。',
    gameplay_summary: '順番に手番を行います。',
    end_game_summary: '勝利条件を満たしたら終了します。',
    source_url: 'https://example.com/rules',
    structured_data: {},
  }

  await page.route('**/api/**', async (route) => {
    const request = route.request()
    const url = new URL(request.url())
    if (url.pathname === '/api/games/game-one' && request.method() === 'GET') {
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(detail) })
      return
    }
    if (url.pathname === '/api/games' && request.method() === 'GET') {
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ games, total: games.length }) })
      return
    }
    await route.fulfill({ status: 404, contentType: 'application/json', body: JSON.stringify({ detail: 'not mocked' }) })
  })
}

test('directory keeps search local, labels controls, exposes mobile filters, and explains compare limit', async ({ page }) => {
  const counters = { generated: 0 }
  await mockDirectory(page, counters)
  await page.goto('/')
  await expect(page.getByText('ゲーム1', { exact: true }).first()).toBeVisible()

  const search = page.getByLabel('ゲームを検索')
  const sort = page.getByLabel('ゲームの並び順')
  await expect(search).toBeVisible()
  await expect(sort).toBeVisible()

  await search.fill('森')
  await search.press('Enter')
  await expect(page.getByText('ゲーム2', { exact: true }).first()).toBeVisible()
  await expect(page.getByText('ゲーム1', { exact: true })).toHaveCount(0)
  expect(counters.generated).toBe(0)

  await search.fill('')
  await expect(page.getByText('ゲーム1', { exact: true }).first()).toBeVisible()

  if ((page.viewportSize()?.width || 0) <= 900) {
    const filterToggle = page.getByRole('button', { name: 'フィルター', exact: true })
    await expect(filterToggle).toBeVisible()
    await filterToggle.click()
    const filterPanel = page.getByRole('dialog', { name: 'ゲーム絞り込み' })
    await expect(filterPanel).toBeVisible()
    await filterPanel.getByRole('button', { name: '2人' }).click()
    await filterPanel.getByRole('button', { name: 'フィルターを閉じる' }).click()
    await expect(page.getByText('人数: 2')).toBeVisible()
    const removePlayerFilter = page.getByRole('button', { name: '人数フィルターを解除' })
    const removeTarget = await removePlayerFilter.boundingBox()
    expect(removeTarget?.width).toBeGreaterThanOrEqual(24)
    expect(removeTarget?.height).toBeGreaterThanOrEqual(24)
    await removePlayerFilter.click()
    await expect(page.getByText('ゲーム2', { exact: true }).first()).toBeVisible()
  }

  for (const title of ['ゲーム1', 'ゲーム2', 'ゲーム3']) {
    await page.getByRole('button', { name: `${title}を比較に追加` }).click()
  }
  await expect(page.getByRole('region', { name: '比較トレイ 3/3' })).toBeVisible()
  await expect(page.getByRole('button', { name: 'ゲーム4を比較に追加' })).toBeDisabled()
  await expect(page.getByText('比較トレイ · 3/3')).toBeVisible()
})

test('public directory search never exposes or sends catalog generation', async ({ page }) => {
  const counters = { generated: 0 }
  await mockDirectory(page, counters)
  await page.goto('/')
  const search = page.getByLabel('ゲームを検索')
  await search.fill('未登録タイトル')
  await search.press('Enter')

  await expect(page.getByText('条件に一致するゲームが見つかりません。')).toBeVisible()
  await expect(page.getByRole('button', { name: '未登録ゲームをAIで追加' })).toHaveCount(0)
  expect(counters.generated).toBe(0)
})

test('game detail secondary views use native buttons with pressed state', async ({ page }) => {
  await mockGameDetail(page)
  await page.goto('/games/game-one')

  await expect(page.getByRole('tablist')).toHaveCount(0)
  await expect(page.getByRole('tab')).toHaveCount(0)
  await expect(page.getByRole('tabpanel')).toHaveCount(0)
  await expect(page.getByRole('group', { name: 'ゲーム詳細表示' })).toHaveCount(1)

  const rulesButton = page.getByRole('button', { name: '詳しいルール', exact: true })
  const setupButton = page.getByRole('button', { name: '準備・流れ・終了', exact: true })
  const relatedButton = page.getByRole('button', { name: '関連ゲーム', exact: true })
  await expect(setupButton).toHaveAttribute('aria-pressed', 'true')
  await expect(rulesButton).toHaveAttribute('aria-pressed', 'false')
  await expect(relatedButton).toHaveAttribute('aria-pressed', 'false')
  await expect(page.getByText('カードを配ります。')).toBeVisible()

  await setupButton.focus()
  await page.keyboard.press('Tab')
  await expect(rulesButton).toBeFocused()
  await page.keyboard.press('Enter')
  await expect(setupButton).toHaveAttribute('aria-pressed', 'false')
  await expect(rulesButton).toHaveAttribute('aria-pressed', 'true')
})
