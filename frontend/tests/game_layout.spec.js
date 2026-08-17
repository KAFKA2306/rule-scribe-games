import { test, expect } from '@playwright/test'

const bigShot = {
  id: 76,
  slug: 'big-shot',
  title: 'Big Shot',
  title_ja: 'ビッグショット',
  min_players: 2,
  max_players: 4,
  play_time: 45,
  min_age: 10,
  published_year: 2001,
  summary: '土地を競り落とし、資金を管理しながら得点を競うオークションゲーム。',
  description: 'Big Shot description',
  setup_summary: '各プレイヤーは開始時の資金を受け取ります。',
  gameplay_summary: '競りで土地を獲得し、資金配分を管理します。',
  end_game_summary: '全区画の競りが終わったら得点を計算します。',
  source_url: 'https://example.com/big-shot-source',
  source_trust: 'third_party',
  content_review_status: 'review_required',
  rules_content: '# Big Shot Rules\n\n## ゲームの流れ\n\n競りを行い、土地を獲得します。\n\n## 得点\n\nゲーム終了時に得点を計算します。',
  structured_data: {
    mechanics: ['Auction / Bidding', 'Area Majority'],
    strategy_analysis: '## Strategy\n\n資金効率を優先します。',
    pro_tips: ['序盤で資金を使い切らない。'],
    rule_mistakes: ['借金の扱いを確認する。'],
    keywords: [{ term: 'Auction', description: '競り' }],
    persona_reviews: [],
  },
}

async function mockGameApi(page, game = bigShot) {
  await page.route('**/api/games**', async route => {
    const url = new URL(route.request().url())
    if (url.pathname === `/api/games/${game.slug}`) {
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ game }) })
      return
    }
    await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ games: [] }) })
  })
}

async function readLayout(page) {
  return page.evaluate(() => {
    const sidebarEl = document.querySelector('.game-sidebar')
    const mainEl = document.querySelector('.game-main')
    const sidebar = sidebarEl?.getBoundingClientRect()
    const main = mainEl?.getBoundingClientRect()
    const title = document.querySelector('.game-title')?.getBoundingClientRect()
    const tabs = document.querySelector('.rules-tabs')?.getBoundingClientRect()
    const readingLine = document.querySelector('.markdown-content p')?.getBoundingClientRect()

    if (!sidebarEl || !mainEl || !sidebar || !main || !title || !tabs || !readingLine) {
      throw new Error('game detail layout nodes are missing')
    }

    return {
      clientWidth: document.documentElement.clientWidth,
      scrollWidth: document.documentElement.scrollWidth,
      sidebar: { x: sidebar.x, y: sidebar.y, width: sidebar.width, height: sidebar.height },
      main: { x: main.x, y: main.y, width: main.width, height: main.height },
      titleX: title.x,
      tabsX: tabs.x,
      readingLine: { x: readingLine.x, width: readingLine.width },
      mainBeforeSidebar: Boolean(mainEl.compareDocumentPosition(sidebarEl) & Node.DOCUMENT_POSITION_FOLLOWING),
    }
  })
}

function expectSinglePrimaryFlow(layout) {
  expect(layout.scrollWidth).toBe(layout.clientWidth)
  expect(layout.mainBeforeSidebar).toBe(true)
  expect(Math.abs(layout.sidebar.x - layout.main.x)).toBeLessThan(2)
  expect(Math.abs(layout.sidebar.width - layout.main.width)).toBeLessThan(2)
  expect(layout.sidebar.y).toBeGreaterThan(layout.main.y + layout.main.height - 2)
  expect(Math.abs(layout.titleX - layout.main.x)).toBeLessThan(2)
  expect(Math.abs(layout.tabsX - layout.main.x)).toBeLessThan(2)
  expect(Math.abs(layout.readingLine.x - layout.main.x)).toBeLessThan(2)
}

test('game detail keeps one primary flow and readable long-form measure', async ({ page }) => {
  await mockGameApi(page)
  await page.setViewportSize({ width: 1280, height: 900 })
  await page.goto('/games/big-shot')

  await expect(page.getByRole('heading', { name: 'ビッグショット' })).toBeVisible()
  await expect(page.getByRole('button', { name: '詳しいルール', exact: true })).toBeVisible()

  const desktop = await readLayout(page)
  expectSinglePrimaryFlow(desktop)
  expect(desktop.main.width).toBeGreaterThan(1000)
  expect(desktop.readingLine.width).toBeLessThan(900)
  expect(desktop.readingLine.width).toBeLessThan(desktop.main.width)

  await page.setViewportSize({ width: 800, height: 900 })
  const compact = await readLayout(page)
  expectSinglePrimaryFlow(compact)
  expect(compact.readingLine.width).toBeLessThanOrEqual(compact.main.width)
  await expect(page.locator('.quick-rules-panel')).toHaveCount(0)
})

test('quick rules flatten to one row on wide desktop inside the single-column page', async ({ page }) => {
  const skullKing = {
    ...bigShot,
    id: 269,
    slug: 'skull-king',
    title: 'Skull King',
    title_ja: 'スカルキング',
  }

  await mockGameApi(page, skullKing)
  await page.setViewportSize({ width: 1280, height: 900 })
  await page.goto('/games/skull-king')

  const cards = page.locator('.quick-rule-card')
  await expect(cards).toHaveCount(4)

  const boxes = await cards.evaluateAll(nodes => nodes.map(node => {
    const rect = node.getBoundingClientRect()
    return { x: rect.x, y: rect.y, width: rect.width }
  }))

  const ys = boxes.map(box => box.y)
  expect(Math.max(...ys) - Math.min(...ys)).toBeLessThan(2)
  expect(boxes.every(box => box.width > 0)).toBe(true)
  expectSinglePrimaryFlow(await readLayout(page))
})

test('game detail uses one native button group after quick rules', async ({ page }) => {
  const skullKing = {
    ...bigShot,
    id: 269,
    slug: 'skull-king',
    title: 'Skull King',
    title_ja: 'スカルキング',
  }

  await mockGameApi(page, skullKing)
  await page.setViewportSize({ width: 1280, height: 900 })
  await page.goto('/games/skull-king')

  await expect(page.locator('.quick-rules-actions')).toHaveCount(0)
  await expect(page.getByRole('tablist')).toHaveCount(0)
  await expect(page.getByRole('tab')).toHaveCount(0)
  await expect(page.getByRole('group', { name: 'ゲーム詳細表示' })).toHaveCount(1)

  const rulesButton = page.getByRole('button', { name: '詳しいルール', exact: true })
  const setupButton = page.getByRole('button', { name: 'セットアップ', exact: true })
  await expect(rulesButton).toHaveAttribute('aria-pressed', 'true')
  await expect(setupButton).toHaveAttribute('aria-pressed', 'false')
  await expect(page.getByRole('button', { name: '図で見る', exact: true })).toHaveCount(1)

  await setupButton.click()
  await expect(rulesButton).toHaveAttribute('aria-pressed', 'false')
  await expect(setupButton).toHaveAttribute('aria-pressed', 'true')
  await expect(page.getByRole('link', { name: /公式出典:/ })).toHaveCount(1)
})

test('setup view shows only game-specific summaries and fails closed when missing', async ({ page }) => {
  await mockGameApi(page)
  await page.goto('/games/big-shot')
  await page.getByRole('button', { name: 'セットアップ', exact: true }).click()

  await expect(page.getByText(bigShot.setup_summary)).toBeVisible()
  await expect(page.getByText(bigShot.gameplay_summary)).toBeVisible()
  await expect(page.getByText(bigShot.end_game_summary)).toBeVisible()
  await expect(page.getByText('公式裁定ではありません。')).toBeVisible()
  await expect(page.getByRole('link', { name: '出典を確認' })).toHaveAttribute('href', bigShot.source_url)
  await expect(page.getByText('初期リソースを配布')).toHaveCount(0)
  await expect(page.getByText('アクションを選択')).toHaveCount(0)
  await expect(page.getByText('リソースを支払う')).toHaveCount(0)

  const missing = {
    ...bigShot,
    setup_summary: null,
    gameplay_summary: null,
    end_game_summary: null,
  }
  await page.unrouteAll({ behavior: 'wait' })
  await mockGameApi(page, missing)
  await page.reload()
  await page.getByRole('button', { name: 'セットアップ', exact: true }).click()

  await expect(page.getByText('このゲーム固有のセットアップ要約は未確認です。')).toBeVisible()
  await expect(page.getByText('このゲーム固有のゲーム進行要約は未確認です。')).toBeVisible()
  await expect(page.getByText('このゲーム固有の終了条件要約は未確認です。')).toBeVisible()
})

test('game share uses Web Share when available', async ({ page }) => {
  await page.addInitScript(() => {
    window.__shared = null
    Object.defineProperty(navigator, 'share', {
      configurable: true,
      value: async data => { window.__shared = data },
    })
  })
  await mockGameApi(page)
  await page.goto('/games/big-shot')

  await page.getByRole('button', { name: '共有', exact: true }).click()
  expect(await page.evaluate(() => window.__shared)).toEqual({
    url: 'https://bodoge-no-mikata.vercel.app/games/big-shot',
  })
  await expect(page.getByRole('button', { name: '共有しました' })).toBeVisible()
})

test('game share copies canonical URL when Web Share is unavailable', async ({ page }) => {
  await page.addInitScript(() => {
    window.__copied = null
    Object.defineProperty(navigator, 'share', { configurable: true, value: undefined })
    Object.defineProperty(navigator, 'clipboard', {
      configurable: true,
      value: { writeText: async text => { window.__copied = text } },
    })
  })
  await mockGameApi(page)
  await page.goto('/games/big-shot')

  await page.getByRole('button', { name: 'リンクをコピー' }).click()
  expect(await page.evaluate(() => window.__copied)).toBe(
    'https://bodoge-no-mikata.vercel.app/games/big-shot',
  )
  await expect(page.getByRole('button', { name: 'コピーしました' })).toBeVisible()
})