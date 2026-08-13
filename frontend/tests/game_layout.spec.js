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

test('game detail keeps a readable desktop main and collapses cleanly at 800px', async ({ page }) => {
  await mockGameApi(page)
  await page.setViewportSize({ width: 1280, height: 900 })
  await page.goto('/games/big-shot')

  await expect(page.getByRole('heading', { name: 'ビッグショット' })).toBeVisible()
  await expect(page.getByRole('tab', { name: 'ANALYSIS & RULES' })).toBeVisible()

  const desktop = await readLayout(page)
  expect(desktop.scrollWidth).toBe(desktop.clientWidth)
  expect(desktop.sidebar.width).toBeGreaterThanOrEqual(280)
  expect(desktop.sidebar.width).toBeLessThanOrEqual(340)
  expect(desktop.main.width).toBeGreaterThan(600)
  expect(desktop.main.x).toBeGreaterThan(desktop.sidebar.x + desktop.sidebar.width)
  expect(desktop.titleX).toBeGreaterThanOrEqual(desktop.main.x)
  expect(desktop.tabsX).toBeGreaterThanOrEqual(desktop.main.x)

  await page.setViewportSize({ width: 800, height: 900 })
  await expect(page.locator('.game-layout')).toHaveCSS('grid-template-columns', /\d+(?:\.\d+)?px/)

  const compact = await readLayout(page)
  expect(compact.scrollWidth).toBe(compact.clientWidth)
  expect(Math.abs(compact.sidebar.x - compact.main.x)).toBeLessThan(2)
  expect(Math.abs(compact.sidebar.width - compact.main.width)).toBeLessThan(2)
  expect(compact.main.y).toBeGreaterThan(compact.sidebar.y + compact.sidebar.height - 2)
})
