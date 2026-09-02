import { test, expect } from '@playwright/test'

async function mockGame(page, game) {
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
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ games: [] }),
    })
  })
}

test('canonical rulesがないゲームはclient側でも基本情報と表示する', async ({ page }) => {
  const game = {
    id: 'game-without-rules',
    slug: 'game-without-rules',
    title: 'Game Without Rules',
    title_ja: 'ルール未確認ゲーム',
    summary: '基本情報だけを確認できるゲームです。',
    identity_status: 'verified',
    source_trust: 'official_publisher',
    content_review_status: 'review_required',
    rules_content: null,
    setup_summary: null,
    gameplay_summary: null,
    end_game_summary: null,
  }

  await mockGame(page, game)
  await page.goto(`/games/${game.slug}`)

  await expect(page).toHaveTitle('「ルール未確認ゲーム」の基本情報 | ボドゲのミカタ')
  await expect(page.getByRole('button', { name: '詳しいルール', exact: true })).toHaveCount(0)
  await expect(page.getByText(game.summary, { exact: true })).toBeVisible()
  await expect(page.getByText('REVIEW REQUIRED', { exact: true })).toBeVisible()

  await page.goto(`/games/${game.slug}#rules`)
  await expect(page.getByRole('button', { name: '詳しいルール', exact: true })).toHaveCount(0)
  await expect(page.getByText(game.summary, { exact: true })).toBeVisible()
})

test('canonical rulesがあるゲームだけclient側でルール要約と表示する', async ({ page }) => {
  const game = {
    id: 'game-with-rules',
    slug: 'game-with-rules',
    title: 'Game With Rules',
    title_ja: 'ルール確認済みゲーム',
    summary: '出典付きルールを確認できるゲームです。',
    identity_status: 'verified',
    source_trust: 'official_publisher',
    content_review_status: 'unknown',
    rules_content: '## セットアップ\n- 準備します。',
    setup_summary: null,
    gameplay_summary: null,
    end_game_summary: null,
  }

  await mockGame(page, game)
  await page.goto(`/games/${game.slug}`)

  await expect(page).toHaveTitle('「ルール確認済みゲーム」のルール・インスト要約 | ボドゲのミカタ')
  await expect(page.getByRole('button', { name: '詳しいルール', exact: true })).toBeVisible()
})
