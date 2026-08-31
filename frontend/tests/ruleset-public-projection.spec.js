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

test('RuleSetがないゲームでは未確認ルールを補完しない', async ({ page }) => {
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
  await expect(page.getByText('公式ルール確認済み', { exact: true })).toHaveCount(0)
  await expect(page.getByText('ルールを質問', { exact: true })).toHaveCount(0)
})

test('RuleSetがあるゲームでもfrontend独自ルールを重ねない', async ({ page }) => {
  await mockGameApi(page, {
    slug: 'splendor',
    title: 'Splendor',
    title_ja: '宝石の煌き',
    summary: '宝石商となって威信ポイントを競うゲーム。',
    rules_content: '# 宝石の煌き\n\n公開RuleSetに基づくルール。',
    setup_summary: null,
    gameplay_summary: null,
    end_game_summary: null,
    min_players: 2,
    max_players: 4,
    play_time: 30,
    min_age: 10,
    source_url: 'https://www.spacecowboys.fr/splendor',
    source_trust: 'official_publisher',
    identity_status: 'verified',
    content_review_status: 'human_reviewed',
    structured_data: {},
  })

  await page.goto('/games/splendor')

  await expect(page.getByRole('heading', { name: '宝石の煌き' })).toBeVisible()
  await expect(page.getByText('公開RuleSetに基づくルール。', { exact: true })).toBeVisible()
  await expect(page.getByText('30秒でわかる「宝石の煌き」', { exact: true })).toHaveCount(0)
  await expect(page.getByText('公式ルール確認済み', { exact: true })).toHaveCount(0)
  await expect(page.getByText('ルールを質問', { exact: true })).toHaveCount(0)
})
