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

async function mockGameApi(page) {
  await page.route('**/api/games**', async route => {
    const url = new URL(route.request().url())
    if (url.pathname === '/api/games/big-shot') {
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ game: bigShot }) })
      return
    }
    await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ games: [] }) })
  })
}

test('desktop game detail uses metadata sidebar plus readable main without page overflow', async ({ page }) => {
  await page.setViewportSize({ width: 1280, height: 900 })
  await mockGameApi(page)
  await page.goto('/games/big-shot')

  await expect(page.getByRole('heading', { name: 'ビッグショット' })).toBeVisible()
  await expect(page.getByRole('tab', { name: 'ANALYSIS & RULES' })).toBeVisible()

  const metrics = await page.evaluate(() => {
    const sidebar = document.querySelector('.game-sidebar').getBoundingClientRect()
    const main = document.querySelector('.game-main').getBoundingClientRect()
    const title = document.querySelector('.game-title').getBoundingClientRect()
    const tabs = document.querySelector('.rules-tabs').getBoundingClientRect()
    return {
      clientWidth: document.documentElement.clientWidth,
      scrollWidth: document.documentElement.scrollWidth,
      sidebar: { x: sidebar.x, y: sidebar.y, width: sidebar.width },
      main: { x: main.x, y: main.y, width: main.width },
      titleX: title.x,
      tabsX: tabs.x,
    }
  })

  expect(metrics.scrollWidth).toBe(metrics.clientWidth)
  expect(metrics.sidebar.width).toBeGreaterThanOrEqual(280)
  expect(metrics.sidebar.width).toBeLessThanOrEqual(340)
  expect(metrics.main.width).toBeGreaterThan(600)
  expect(metrics.main.x).toBeGreaterThan(metrics.sidebar.x + metrics.sidebar.width)
  expect(metrics.titleX).toBeGreaterThanOrEqual(metrics.main.x)
  expect(metrics.tabsX).toBeGreaterThanOrEqual(metrics.main.x)
})

test('game detail collapses to one column at 800px', async ({ page }) => {
  await page.setViewportSize({ width: 800, height: 900 })
  await mockGameApi(page)
  await page.goto('/games/big-shot')

  const metrics = await page.evaluate(() => {
    const sidebar = document.querySelector('.game-sidebar').getBoundingClientRect()
    const main = document.querySelector('.game-main').getBoundingClientRect()
    return {
      clientWidth: document.documentElement.clientWidth,
      scrollWidth: document.documentElement.scrollWidth,
      sidebar: { x: sidebar.x, y: sidebar.y, width: sidebar.width },
      main: { x: main.x, y: main.y, width: main.width },
    }
  })

  expect(metrics.scrollWidth).toBe(metrics.clientWidth)
  expect(Math.abs(metrics.sidebar.x - metrics.main.x)).toBeLessThan(2)
  expect(Math.abs(metrics.sidebar.width - metrics.main.width)).toBeLessThan(2)
  expect(metrics.main.y).toBeGreaterThan(metrics.sidebar.y)
})
