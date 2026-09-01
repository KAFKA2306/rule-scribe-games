import { test, expect } from '@playwright/test'

const game = {
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
  source_url: 'https://example.com/big-shot-source',
  source_trust: 'third_party',
  identity_status: 'verified',
  content_review_status: 'review_required',
  bgg_url: 'https://boardgamegeek.com/boardgame/1/example',
  rules_content: '# Big Shot Rules\n\nルール本文。',
}

test('出典リンクと信頼状態を同じ表示で確認できる', async ({ page }) => {
  await page.route('**/api/games**', async route => {
    const url = new URL(route.request().url())
    if (url.pathname === `/api/games/${game.slug}`) {
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ game }) })
      return
    }
    await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ games: [] }) })
  })

  await page.goto('/games/big-shot')

  const panel = page.getByLabel('出典・根拠')
  await expect(panel).toHaveCount(1)
  await expect(panel.getByText('IDENTITY VERIFIED')).toBeVisible()
  await expect(panel.getByText('THIRD-PARTY SOURCE')).toBeVisible()
  await expect(panel.getByText('REVIEW REQUIRED')).toBeVisible()
  await expect(panel.getByRole('link', { name: '第三者の出典' })).toHaveAttribute('href', game.source_url)
  await expect(panel.getByRole('link', { name: 'BoardGameGeek' })).toHaveAttribute('href', game.bgg_url)

  await expect(page.getByText('TRUST & PROVENANCE')).toHaveCount(0)
  await expect(page.getByText('LINKS', { exact: true })).toHaveCount(0)
})
