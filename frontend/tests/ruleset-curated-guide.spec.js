import { test, expect } from '@playwright/test'

async function mockGameApi(page, game) {
  await page.route('**/api/games**', async route => {
    const url = new URL(route.request().url())
    if (url.pathname === `/api/games/${game.slug}`) {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ game }),
      })
      return
    }
    await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ games: [] }) })
  })
}

test('RuleSetが公開されていないゲームではcurated guideを表示しない', async ({ page }) => {
  await mockGameApi(page, {
    slug: 'minna-de-ponkotsu-paint',
    title: 'みんなでぽんこつペイント',
    title_ja: 'みんなでぽんこつペイント',
    summary: '公式商品情報に基づくゲーム概要。',
    rules_content: null,
    setup_summary: null,
    gameplay_summary: null,
    end_game_summary: null,
    min_players: 2,
    max_players: 12,
    play_time: 10,
    min_age: 6,
    published_year: 2018,
    source_url: 'https://hobbyjapan.games/ponkotsu_paint/',
    source_trust: 'official_publisher',
    identity_status: 'verified',
    content_review_status: 'review_required',
    structured_data: {},
  })

  await page.goto('/games/minna-de-ponkotsu-paint')

  await expect(page.getByRole('heading', { name: 'みんなでぽんこつペイント' })).toBeVisible()
  await expect(page.getByText('「みんなでぽんこつペイント」のゲーム概要', { exact: true })).toBeVisible()
  await expect(page.getByText('30秒でわかる「みんなでぽんこつペイント」', { exact: true })).toHaveCount(0)
  await expect(page.locator('.quick-rules-panel')).toHaveCount(0)
  await expect(page.getByRole('button', { name: '図で見る', exact: true })).toHaveCount(0)
})

test('公開RuleSetがあるゲームではcurated guideを維持する', async ({ page }) => {
  await mockGameApi(page, {
    slug: 'skull-king',
    title: 'Skull King',
    title_ja: 'スカルキング',
    summary: 'トリックテイキングゲーム。',
    rules_content: '# スカルキング\n\n公開RuleSetに基づくルール。',
    setup_summary: null,
    gameplay_summary: null,
    end_game_summary: null,
    min_players: 2,
    max_players: 8,
    play_time: 30,
    min_age: 8,
    source_url: 'https://www.grandpabecksgames.com/pages/skull-king',
    source_trust: 'official_publisher',
    identity_status: 'verified',
    content_review_status: 'human_reviewed',
    structured_data: {},
  })

  await page.goto('/games/skull-king')

  await expect(page.getByText('30秒でわかる「スカルキング」', { exact: true })).toBeVisible()
  await expect(page.locator('.quick-rules-panel')).toHaveCount(1)
  await expect(page.getByRole('button', { name: '図で見る', exact: true })).toHaveCount(1)
})
