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
  await expect(page.getByText('「ビッグショット」のゲーム概要', { exact: true })).toBeVisible()
  await expect(page.getByText('30秒でわかる「ビッグショット」', { exact: true })).toHaveCount(0)
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

test('game page title advertises strategy only when strategy content exists', async ({ page }) => {
  await mockGameApi(page)
  await page.goto('/games/big-shot')
  await expect(page).toHaveTitle('「ビッグショット」のルール・戦略・インスト要約 | ボドゲのミカタ')
})

test('game page title omits strategy when strategy content is absent', async ({ page }) => {
  const withoutStrategy = {
    ...bigShot,
    slug: 'no-strategy',
    title_ja: '戦略なしゲーム',
    structured_data: {
      ...bigShot.structured_data,
      strategy_analysis: null,
    },
  }

  await mockGameApi(page, withoutStrategy)
  await page.goto('/games/no-strategy')
  await expect(page).toHaveTitle('「戦略なしゲーム」のルール・インスト要約 | ボドゲのミカタ')
})

test('game detail uses one native button group for canonical game detail views', async ({ page }) => {
  await mockGameApi(page)
  await page.setViewportSize({ width: 1280, height: 900 })
  await page.goto('/games/big-shot')

  await expect(page.locator('.quick-rules-actions')).toHaveCount(0)
  await expect(page.getByRole('tablist')).toHaveCount(0)
  await expect(page.getByRole('tab')).toHaveCount(0)
  await expect(page.getByRole('group', { name: 'ゲーム詳細表示' })).toHaveCount(1)

  const rulesButton = page.getByRole('button', { name: '詳しいルール', exact: true })
  const flowButton = page.getByRole('button', { name: '準備・流れ・終了', exact: true })
  await expect(rulesButton).toHaveAttribute('aria-pressed', 'true')
  await expect(flowButton).toHaveAttribute('aria-pressed', 'false')

  await flowButton.click()
  await expect(rulesButton).toHaveAttribute('aria-pressed', 'false')
  await expect(flowButton).toHaveAttribute('aria-pressed', 'true')
  await expect(page.getByRole('link', { name: '出典を確認' })).toHaveAttribute('href', bigShot.source_url)
})

test('preparation flow only appears when at least one game-specific summary exists', async ({ page }) => {
  await mockGameApi(page)
  await page.goto('/games/big-shot')
  await page.getByRole('button', { name: '準備・流れ・終了', exact: true }).click()

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

  await expect(page.getByRole('button', { name: '準備・流れ・終了', exact: true })).toHaveCount(0)
  await expect(page.getByText('このゲーム固有のセットアップ要約は未確認です。')).toHaveCount(0)
  await expect(page.getByText('このゲーム固有のゲーム進行要約は未確認です。')).toHaveCount(0)
  await expect(page.getByText('このゲーム固有の終了条件要約は未確認です。')).toHaveCount(0)

  const partial = {
    ...bigShot,
    setup_summary: null,
    gameplay_summary: null,
  }
  await page.unrouteAll({ behavior: 'wait' })
  await mockGameApi(page, partial)
  await page.reload()
  await page.getByRole('button', { name: '準備・流れ・終了', exact: true }).click()

  await expect(page.getByText('このゲーム固有のセットアップ要約は未確認です。')).toBeVisible()
  await expect(page.getByText('このゲーム固有のゲーム進行要約は未確認です。')).toBeVisible()
  await expect(page.getByText(bigShot.end_game_summary)).toBeVisible()
})

test('empty strategy and review states are not exposed as detail destinations', async ({ page }) => {
  const withoutOptionalContent = {
    ...bigShot,
    slug: 'empty-optional-content',
    structured_data: {
      ...bigShot.structured_data,
      strategy_analysis: null,
      persona_reviews: [],
    },
  }

  await mockGameApi(page, withoutOptionalContent)
  await page.goto('/games/empty-optional-content')

  await expect(page.getByRole('button', { name: '戦略', exact: true })).toHaveCount(0)
  await expect(page.getByRole('button', { name: 'レビュー', exact: true })).toHaveCount(0)
  await expect(page.getByText('戦略解説はまだ登録されていません。', { exact: true })).toHaveCount(0)
  await expect(page.getByText('レビューはまだ登録されていません。', { exact: true })).toHaveCount(0)
  await expect(page.getByText(/再生成してください/)).toHaveCount(0)
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
    title: '「ビッグショット」のルール・戦略・インスト要約 | ボドゲのミカタ',
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

test('X share copy stays factual and uses the canonical game URL', async ({ page }) => {
  await page.addInitScript(() => {
    window.__openedShareUrl = null
    window.open = (url) => {
      window.__openedShareUrl = url
      return null
    }
  })
  await mockGameApi(page)
  await page.goto('/games/big-shot')

  await page.getByRole('button', { name: 'Xで共有' }).click()
  const shareUrl = await page.evaluate(() => window.__openedShareUrl)
  const parsed = new URL(shareUrl)
  expect(parsed.searchParams.get('text')).toBe('ボードゲーム「ビッグショット」のルールを見る')
  expect(parsed.searchParams.get('url')).toBe('https://bodoge-no-mikata.vercel.app/games/big-shot')
  expect(parsed.searchParams.get('text')).not.toContain('3分')
})

test('text-to-speech control identifies that it reads page highlights', async ({ page }) => {
  await page.addInitScript(() => {
    Object.defineProperty(window, 'speechSynthesis', {
      configurable: true,
      value: { cancel() {}, speak() {} },
    })
  })
  await mockGameApi(page)
  await page.goto('/games/big-shot')

  await expect(page.getByRole('button', { name: 'ページの要点を読み上げ' })).toBeVisible()
  await expect(page.getByRole('button', { name: 'Text to speech' })).toHaveCount(0)
})
