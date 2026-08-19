import { test, expect } from '@playwright/test'

const game = {
  id: 'source-links-game',
  slug: 'source-links-game',
  title: 'Source Links Game',
  title_ja: '出典リンクテスト',
  min_players: 2,
  max_players: 4,
  play_time: 30,
  min_age: 8,
  published_year: 2025,
  summary: '出典リンク表示のテスト用ゲーム。',
  description: 'Source link test game',
  rules_content: '# Rules',
  source_url: 'https://publisher.example/rules',
  source_trust: 'official_publisher',
  content_review_status: 'review_required',
  identity_status: 'verified',
  bgg_url: 'https://boardgamegeek.com/boardgame/1/example',
  bga_url: 'https://boardgamearena.com/gamepanel?game=example',
  structured_data: {},
}

async function mockGameApi(page, value = game) {
  await page.route('**/api/games**', async route => {
    const url = new URL(route.request().url())
    if (url.pathname === `/api/games/${value.slug}`) {
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ game: value }) })
      return
    }
    await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ games: [] }) })
  })
}

test('registered source is separate from community and play links', async ({ page }) => {
  await mockGameApi(page)
  await page.goto('/games/source-links-game')

  const sourceGroup = page.locator('[aria-label="登録済み出典"]')
  const otherGroup = page.locator('[aria-label="その他のリンク"]')

  await expect(sourceGroup.getByRole('link', { name: '出版社のページ' })).toHaveAttribute('href', game.source_url)
  await expect(sourceGroup.getByRole('link', { name: 'BoardGameGeek' })).toHaveCount(0)
  await expect(sourceGroup.getByRole('link', { name: 'Board Game Arena' })).toHaveCount(0)
  await expect(otherGroup.getByRole('link', { name: 'BoardGameGeek' })).toHaveAttribute('href', game.bgg_url)
  await expect(otherGroup.getByRole('link', { name: 'Board Game Arena' })).toHaveAttribute('href', game.bga_url)
  await expect(page.getByText('REVIEW REQUIRED', { exact: true })).toBeVisible()
})

test('missing registered source does not create an empty source group', async ({ page }) => {
  const withoutSource = { ...game, source_url: null, source_trust: 'unknown' }
  await mockGameApi(page, withoutSource)
  await page.goto('/games/source-links-game')

  await expect(page.locator('[aria-label="登録済み出典"]')).toHaveCount(0)
  await expect(page.locator('[aria-label="その他のリンク"]')).toBeVisible()
})
