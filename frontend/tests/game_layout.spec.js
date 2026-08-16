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
    if (url.pathname === '/api/games/big-shot') {
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ game }) })
      return
    }
    await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ games: [] }) })
  })
}

async function readLayout(page) {
  return page.evaluate(() => {
    const sidebar = document.querySelector('.game-sidebar')?.getBoundingClientRect()
    const main = document.querySelector('.game-main')?.getBoundingClientRect()
    const title = document.querySelector('.game-title')?.getBoundingClientRect()
    const tabs = document.querySelector('.rules-tabs')?.getBoundingClientRect()

    if (!sidebar || !main || !title || !tabs) throw new Error('game detail layout nodes are missing')

    return {
      clientWidth: document.documentElement.clientWidth,
      scrollWidth: document.documentElement.scrollWidth,
      sidebar: { x: sidebar.x, y: sidebar.y, width: sidebar.width, height: sidebar.height },
      main: { x: main.x, y: main.y, width: main.width, height: main.height },
      titleX: title.x,
      tabsX: tabs.x,
    }
  })
}

function expectSingleColumn(layout) {
  expect(layout.scrollWidth).toBe(layout.clientWidth)
  expect(Math.abs(layout.sidebar.x - layout.main.x)).toBeLessThan(2)
  expect(Math.abs(layout.sidebar.width - layout.main.width)).toBeLessThan(2)
  expect(layout.sidebar.y).toBeGreaterThan(layout.main.y + layout.main.height - 2)
  expect(layout.titleX).toBeGreaterThanOrEqual(layout.main.x)
  expect(layout.tabsX).toBeGreaterThanOrEqual(layout.main.x)
}

test('game detail stays single-column at desktop and compact widths', async ({ page }) => {
  await mockGameApi(page)
  await page.setViewportSize({ width: 1280, height: 900 })
  await page.goto('/games/big-shot')

  await expect(page.getByRole('heading', { name: 'ビッグショット' })).toBeVisible()
  await expect(page.getByRole('tab', { name: /詳しいルール/ })).toBeVisible()

  const desktop = await readLayout(page)
  expectSingleColumn(desktop)
  expect(desktop.main.width).toBeGreaterThan(1000)

  await page.setViewportSize({ width: 800, height: 900 })
  await expect(page.locator('.game-layout')).toHaveCSS('grid-template-columns', /\d+(?:\.\d+)?px/)

  const compact = await readLayout(page)
  expectSingleColumn(compact)
  await expect(page.getByText('検証済みの要約はまだありません')).toBeVisible()
})

test('setup tab shows only game-specific summaries and fails closed when missing', async ({ page }) => {
  await mockGameApi(page)
  await page.goto('/games/big-shot')
  await page.getByRole('tab', { name: /セットアップ/ }).click()

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
  await page.getByRole('tab', { name: /セットアップ/ }).click()

  await expect(page.getByText('このゲーム固有のセットアップ要約は未確認です。')).toBeVisible()
  await expect(page.getByText('このゲーム固有のゲーム進行要約は未確認です。')).toBeVisible()
  await expect(page.getByText('このゲーム固有の終了条件要約は未確認です。')).toBeVisible()
})
